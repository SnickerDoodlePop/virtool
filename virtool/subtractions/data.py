import asyncio
import math
import shutil
from asyncio import CancelledError, to_thread
from logging import getLogger
from typing import Optional

from aiohttp import MultipartReader
import os
from multidict import MultiDictProxy
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from virtool_core.models.subtraction import (
    Subtraction,
    SubtractionSearchResult,
    SubtractionFile,
)
from virtool_core.utils import rm, compress_file

import virtool.mongo.utils
import virtool.subtractions.files
import virtool.utils
from virtool.api.utils import compose_regex_query
from virtool.config import Config
from virtool.data.errors import ResourceNotFoundError, ResourceConflictError
from virtool.data.events import emits, Operation
from virtool.data.file import FileDescriptor
from virtool.data.piece import DataLayerPiece
from virtool.jobs.utils import JobRights
from virtool.jobs.db import lookup_minimal_job_by_id
from virtool.users.db import lookup_nested_user_by_id
from virtool.mongo.utils import get_new_id, get_one_field
from virtool.pg.utils import get_row_by_id
from virtool.subtractions.db import (
    attach_computed,
    unlink_default_subtractions,
    check_subtraction_fasta_files,
)
from virtool.subtractions.models import SQLSubtractionFile
from virtool.subtractions.oas import (
    CreateSubtractionRequest,
    UpdateSubtractionRequest,
    FinalizeSubtractionRequest,
)
from virtool.subtractions.utils import (
    join_subtraction_path,
    FILES,
    check_subtraction_file_type,
    join_subtraction_index_path,
)
from virtool.tasks.progress import (
    AbstractProgressHandler,
    AccumulatingProgressHandlerWrapper,
)
from virtool.uploads.models import SQLUpload
from virtool.uploads.utils import naive_writer
from virtool.utils import base_processor

logger = getLogger(__name__)


class SubtractionsData(DataLayerPiece):
    name = "subtractions"

    def __init__(self, base_url: str, config: Config, mongo, pg: AsyncEngine):
        self._base_url = base_url
        self._config = config
        self._mongo = mongo
        self._pg = pg

    async def find(self, find: str, short: bool, ready: bool, query: MultiDictProxy):
        db_query = {}

        if find:
            db_query = compose_regex_query(find, ["name", "nickname"])

        if ready:
            db_query["ready"] = True

        if short:
            return [
                base_processor(document)
                async for document in self._mongo.subtraction.find(
                    {**db_query, "deleted": False}, ["name", "ready"]
                ).sort("name")
            ]

        page = int(query.get("page", 1))
        per_page = int(query.get("per_page", 25))

        data = await self._mongo.subtraction.aggregate(
            [
                {"$match": {"deleted": False}},
                {
                    "$facet": {
                        "total_count": [{"$count": "total_count"}],
                        "ready_count": [
                            {"$match": {"ready": True}},
                            {"$count": "ready_count"},
                        ],
                        "found_count": [
                            {"$match": db_query},
                            {"$count": "found_count"},
                        ],
                        "documents": [
                            {"$match": db_query},
                            {"$sort": {"name": 1}},
                            {"$skip": per_page * (page - 1)},
                            {"$limit": per_page},
                            *lookup_nested_user_by_id(local_field="user.id"),
                            *lookup_minimal_job_by_id(local_field="job.id"),
                            {
                                "$project": {
                                    "id": "$_id",
                                    "_id": False,
                                    "count": True,
                                    "created_at": True,
                                    "file": True,
                                    "ready": True,
                                    "job": True,
                                    "name": True,
                                    "nickname": True,
                                    "user": True,
                                    "subtraction_id": True,
                                    "gc": True,
                                }
                            },
                        ],
                    }
                },
                {
                    "$project": {
                        "documents": True,
                        "total_count": {
                            "$ifNull": [
                                {"$arrayElemAt": ["$total_count.total_count", 0]},
                                0,
                            ]
                        },
                        "found_count": {
                            "$ifNull": [
                                {"$arrayElemAt": ["$found_count.found_count", 0]},
                                0,
                            ]
                        },
                        "ready_count": {
                            "$ifNull": [
                                {"$arrayElemAt": ["$ready_count.ready_count", 0]},
                                0,
                            ]
                        },
                    }
                },
            ]
        ).to_list(length=1)

        if len(data) == 0:
            raise ResourceNotFoundError

        data = data[0]

        return SubtractionSearchResult(
            **data,
            page=page,
            per_page=per_page,
            page_count=math.ceil(data["found_count"] / per_page),
        )

    @emits(Operation.CREATE)
    async def create(
        self,
        data: CreateSubtractionRequest,
        user_id: str,
        space_id: int,
        subtraction_id: Optional[str] = None,
    ) -> Subtraction:
        """
        Create a new subtraction.
        :param data: a subtraction creation request
        :param user_id: the id of the creating user
        :param space_id: the id of the subtraction's parent space
        :param subtraction_id: the id of the subtraction
        :return: the subtraction
        """

        upload = await get_row_by_id(self._pg, SQLUpload, data.upload_id)

        if upload is None:
            raise ResourceNotFoundError("Upload does not exist")

        job_id = await get_new_id(self._mongo.jobs)

        document = await self._mongo.subtraction.insert_one(
            {
                "_id": subtraction_id
                or await virtool.mongo.utils.get_new_id(self._mongo.subtraction),
                "count": None,
                "created_at": virtool.utils.timestamp(),
                "deleted": False,
                "file": {"id": upload.id, "name": upload.name},
                "gc": None,
                "job": {"id": job_id},
                "name": data.name,
                "nickname": data.nickname,
                "ready": False,
                "space": {"id": space_id},
                "upload": data.upload_id,
                "user": {"id": user_id},
            }
        )

        subtraction = await self.get(document["_id"])

        await self.data.jobs.create(
            "create_subtraction",
            {
                "subtraction_id": subtraction.id,
                "files": [{"id": upload.id, "name": upload.name}],
            },
            user_id,
            JobRights(),
            0,
            job_id,
        )

        return subtraction

    async def get(self, subtraction_id: str) -> Subtraction:
        document = await self._mongo.subtraction.aggregate(
            [
                {"$match": {"_id": subtraction_id}},
                {
                    "$project": {
                        "_id": True,
                        "count": True,
                        "created_at": True,
                        "file": True,
                        "ready": True,
                        "job": True,
                        "name": True,
                        "nickname": True,
                        "user": True,
                        "subtraction_id": True,
                        "gc": True,
                    }
                },
                *lookup_nested_user_by_id(local_field="user.id"),
                *lookup_minimal_job_by_id(local_field="job.id"),
            ]
        ).to_list(length=1)

        if len(document) != 0:
            document = await attach_computed(
                self._mongo, self._pg, self._base_url, document[0]
            )

            document = base_processor(document)

            return Subtraction(**document)

        raise ResourceNotFoundError

    @emits(Operation.UPDATE)
    async def update(
        self, subtraction_id: str, data: UpdateSubtractionRequest
    ) -> Subtraction:
        data = data.dict(exclude_unset=True)

        update = {}

        if "name" in data:
            update["name"] = data["name"]

        if "nickname" in data:
            update["nickname"] = data["nickname"]

        document = await self._mongo.subtraction.find_one_and_update(
            {"_id": subtraction_id}, {"$set": update}
        )

        if document is None:
            raise ResourceNotFoundError

        return await self.get(subtraction_id)

    async def delete(self, subtraction_id: str):
        async with self._mongo.create_session() as session:
            update_result = await self._mongo.subtraction.update_one(
                {"_id": subtraction_id, "deleted": False},
                {"$set": {"deleted": True}},
                session=session,
            )

            if update_result.modified_count == 0:
                raise ResourceNotFoundError

            await asyncio.gather(
                unlink_default_subtractions(self._mongo, subtraction_id, session),
                to_thread(
                    shutil.rmtree,
                    join_subtraction_path(self._config, subtraction_id),
                    True,
                ),
            )

        return update_result.modified_count

    @emits(Operation.UPDATE)
    async def finalize(self, subtraction_id: str, data: FinalizeSubtractionRequest):
        """
        Finalize a subtraction.

        This sets values for the `results` and `gc` fields and switches the `ready`
        field to `true`.

        :param subtraction_id:
        :param data:
        :return:
        """
        ready = await get_one_field(self._mongo.subtraction, "ready", subtraction_id)

        if ready:
            raise ResourceConflictError("Subtraction has already been finalized")

        subtraction = await self._mongo.subtraction.update_one(
            {"_id": subtraction_id}, {"$set": {**data.dict(), "ready": True}}
        )

        if subtraction:
            return await self.get(subtraction_id)

        raise ResourceNotFoundError

    async def upload_file(
        self, subtraction_id: str, filename: str, reader: MultipartReader
    ) -> SubtractionFile:
        """
        Handle a subtraction file upload.

        Takes the ``subtraction_id`` for the subtraction the file should be associated
        with and a ``filename`` for the file. A ``ResourceConflictError`` is raised if a
        file with the same ``filename`` already exists.

        The upload is executed by passing in the ``MultipartReader`` from the upload
        request.

        :param subtraction_id: the id of the subtraction
        :param filename: the name of the file
        :param reader: the multipart reader containing the file content
        :return: the subtraction file resource model
        """
        document = await self._mongo.subtraction.find_one(subtraction_id)

        if document is None:
            raise ResourceNotFoundError

        if filename not in FILES:
            raise ResourceNotFoundError("Unsupported subtraction file name")

        file_type = check_subtraction_file_type(filename)

        path = self._config.data_path / "subtractions" / subtraction_id / filename

        try:
            async with AsyncSession(self._pg) as session:
                subtraction_file = SQLSubtractionFile(
                    name=filename, subtraction=subtraction_id, type=file_type
                )

                session.add(subtraction_file)

                try:
                    await session.flush()
                except IntegrityError:
                    raise ResourceConflictError("File name already exists")

                size = await naive_writer(reader, path)

                subtraction_file.size = size
                subtraction_file.uploaded_at = virtool.utils.timestamp()
                subtraction_file.ready = True

                session.add(subtraction_file)

                subtraction_file_dict = subtraction_file.to_dict()

                await session.commit()
        except CancelledError:
            await to_thread(
                rm, self._config.data_path / "subtractions" / subtraction_id / filename
            )

        return SubtractionFile(
            **subtraction_file_dict,
            download_url=f"{self._base_url}/subtractions/{subtraction_id}/files/{filename}",
        )

    async def get_file(self, subtraction_id: str, filename: str):
        document = await self._mongo.subtraction.find_one(subtraction_id)

        if document is None or filename not in FILES:
            raise ResourceNotFoundError

        async with AsyncSession(self._pg) as session:
            result = (
                await session.execute(
                    select(SQLSubtractionFile).filter_by(
                        subtraction=subtraction_id, name=filename
                    )
                )
            ).scalar()

        if not result:
            raise ResourceNotFoundError

        file = result.to_dict()

        path = join_subtraction_path(self._config, subtraction_id) / filename

        if not await to_thread(path.is_file):
            logger.warning("")
            raise ResourceNotFoundError

        return FileDescriptor(path=path, size=file["size"])

    async def generate_fasta_file(self, subtraction_id: str):
        """
        Generate a FASTA file for a subtraction that has Bowtie2 index files, but no
        FASTA file.

        """
        index_path = join_subtraction_index_path(self._config, subtraction_id)

        fasta_path = (
            join_subtraction_path(self._config, subtraction_id) / "subtraction.fa"
        )

        proc = await asyncio.create_subprocess_shell(
            f"bowtie2-inspect {index_path} > {fasta_path}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )

        await proc.communicate()

        target_path = (
            join_subtraction_path(self._config, subtraction_id) / "subtraction.fa.gz"
        )

        await to_thread(compress_file, fasta_path, target_path)
        await to_thread(rm, fasta_path)

    async def rename_and_track_files(self, progress_handler: AbstractProgressHandler):
        """
        Rename index files and add a ``files`` field to any legacy subtractions.

        Changes Bowtie2 index name from 'reference' to 'subtraction'.

        """
        count = await self._mongo.subtraction.count_documents({"deleted": False})

        tracker = AccumulatingProgressHandlerWrapper(progress_handler, count)

        async for subtraction in self._mongo.subtraction.find({"deleted": False}):
            subtraction_id = subtraction["_id"]

            path = join_subtraction_path(self._config, subtraction_id)

            await virtool.subtractions.utils.rename_bowtie_files(path)

            subtraction_files = []

            for filename in sorted(await to_thread(os.listdir, path)):
                if filename in FILES:
                    async with AsyncSession(self._pg) as session:
                        exists = (
                            await session.execute(
                                select(SQLSubtractionFile).filter_by(
                                    subtraction=subtraction_id, name=filename
                                )
                            )
                        ).scalar()

                    if not exists:
                        subtraction_files.append(filename)

            await virtool.subtractions.files.create_subtraction_files(
                self._pg, subtraction_id, subtraction_files, path
            )

            await tracker.add(1)

    async def check_fasta_files(self):
        """
        Check that all subtractions have a FASTA file.

        If a subtraction has Bowtie2 index files but no FASTA file, generate one.

        """
        return await check_subtraction_fasta_files(self._mongo, self._config)
