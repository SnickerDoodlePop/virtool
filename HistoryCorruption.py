import pymongo
from pymongo import MongoClient


class EmptyHistoryRecords(Exception):
    pass

    
def expandRecordsByVersion(records: list) -> list:
    expanded_records = [None]

    for record in records:
        version: int | str = record["otu"]["version"]

        if version == "removed":
            expanded_records.append(record)

        else:
            while len(expanded_records) < version:
                expanded_records = expanded_records + ([None] * len(expanded_records))
            
            expanded_records.insert(version, record)

    return expanded_records




def historyIsCorrupted(records: list) -> bool:
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

    del history

    # sort history record groups by otu version
    for key in groupedHistoryRecords:
        groupedHistoryRecords[key] = sorted(
            groupedHistoryRecords[key], key=getComparableOrderKey
        )

    # filter only corrupted history records
    corruptedHistoryRecords = {
        key: value
        for (key, value) in groupedHistoryRecords.items()
        if historyIsCorrupted(value)
    }

    expanded_corrupted_history_records = {
        key: expandRecordsByVersion(value)
        for (key, value) in corruptedHistoryRecords.items()
    }

    del groupedHistoryRecords, corruptedHistoryRecords

    for value in expanded_corrupted_history_records.values():
        for (index, record) in enumerate(value):
            if record is None:
                print(f"{index}: No Record")

            else:
                print("{}, {}".format(index, record["_id"]))

        print("END OF HISTORY")
        print("==============")
