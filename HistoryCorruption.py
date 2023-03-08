import pymongo
from pymongo import MongoClient


class CorruptedHistoryRecords:
    def __init__(self, records=None) -> None:
        if records is None:
            records = []

        self.records = records
        self.corruption_level = getCorruptionLevel(records=records)


def getCorruptionLevel(records=None) -> int:
    if records is None:
        records = []

    if len(records) == 0:
        return 0

    return len(records) - records[-1]["otu"]["version"]


def identifyIsCorrupted(records: list) -> bool:
    for idx, record in enumerate(records):
        version = record["otu"]["version"]

        if version == "removed":
            return False if idx == (len(records) - 1) else True

        elif version != idx:
            return True

        else:
            continue

    return False


def getComparableOrderKey(record):
    order = record["_id"].split(".")

    if order[-1] == "removed":
        return int(0xFFFFFFFF)
    else:
        return int(order[-1])


def getDBClient(address: str, port: int, maxPoolSize: int = 50) -> MongoClient:
    return pymongo.MongoClient("localhost", 27017, maxPoolSize=50)


def main(args: list[str]) -> None:
    # cmd and debug arg parsing
    debugArgs: list[str] = []

    args.extend(debugArgs)

    if len(args) > 1:
        print(f"Running HistoryCorruption with args:\n {args}")

    # connect to db
    client: MongoClient = getDBClient(address="localhost", port=27017)

    history = client.get_database("virtool").get_collection("history")

    groupedHistoryRecords: dict = {}

    # organize history records by integer component of `_id` field
    for record in list(history.find()):
        recordID = record.get("_id").split(".")[0]

        try:
            # will throw KeyError if no list has been defined
            groupedHistoryRecords[recordID].append(record)

        except KeyError:
            groupedHistoryRecords[recordID] = []
            groupedHistoryRecords[recordID].append(record)

    del history, record, recordID

    # sort history record groups by otu version
    for key in groupedHistoryRecords:
        groupedHistoryRecords[key] = sorted(
            groupedHistoryRecords[key], key=getComparableOrderKey
        )

    # filter only corrupted history records
    corruptedHistoryRecords = {
        key: value
        for (key, value) in groupedHistoryRecords.items()
        if identifyIsCorrupted(value)
    }

    del groupedHistoryRecords, key

    pass
