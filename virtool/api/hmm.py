import asyncio

import virtool.db.hmm
import virtool.hmm
import virtool.utils
from virtool.api.utils import compose_regex_query, json_response, not_found, paginate, protected


async def find(req):
    """
    Find HMM annotation documents.

    """

    db = req.app["db"]

    term = req.query.get("find", None)

    db_query = dict()

    if term:
        db_query.update(compose_regex_query(term, ["names"]))

    data = await paginate(
        db.hmm,
        db_query,
        req.query,
        sort="cluster",
        projection=virtool.hmm.PROJECTION,
        base_query={"hidden": False}
    )

    data["file_exists"] = virtool.hmm.file_exists(req.app["settings"].get("data_path"))

    return json_response(data)


async def get(req):
    """
    Get a complete individual HMM annotation document.

    """
    document = await req.app["db"].hmm.find_one({"_id": req.match_info["hmm_id"]})

    if document is None:
        return not_found()

    return json_response(virtool.utils.base_processor(document))


async def get_install(req):
    """
    Get the HMM install document. Create one first if none exists.

    """
    document = await virtool.db.hmm.find_and_ensure_install(req.app["db"])

    return json_response(virtool.utils.base_processor(document))


@protected("modify_hmm")
async def install(req):
    """
    Install the official HMM database from GitHub.

    """
    db = req.app["db"]

    document = await virtool.db.hmm.find_and_ensure_install(req.app["db"], reset=True)

    asyncio.ensure_future(virtool.hmm.install_official(
        req.app.loop,
        db,
        req.app["settings"],
        req.app["dispatcher"].dispatch,
        req.app["version"]
    ), loop=req.app.loop)

    return json_response(virtool.utils.base_processor(document))
