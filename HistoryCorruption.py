import pymongo
from pymongo import MongoClient


class EmptyHistoryRecords(Exception):
    pass


def reconstructRecordFromDiff(record: dict = {}) -> dict:
    lost_record = {}

def canBeRestored(records: list = []) -> bool:
    for index, record in enumerate(records):
        # if history record is missing
        if record is None:
            try:
                if index == (len(records) - 1):
                    return False
                
                elif records[index - 1] is None:
                    return False

                else:
                    continue

            # first history record is missing; check next
            except IndexError:
                continue

        else:
            continue

    return True


def expandRecordIDXByVersion(records: list = []) -> list:
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
        # big number lol
        return int(0xFFFFFFFF)
    else:
        return int(order[-1])


def main(args: list[str]) -> None:
    if len(args) > 1:
        print(f"Running HistoryCorruption with args:\n {args}")


    
    # ---------------------------------------------------------------------- #
    # obtaining and sorting the otu history records

    # connect to db
    client: MongoClient = pymongo.MongoClient("localhost", 27017, maxPoolSize=50)

    # grab the otu history records
    history = client.get_database("virtool").get_collection("history")

    grouped_history_records: dict = {}

    # organize history records by otu id
    for record in list(history.find()):
        otuID = record.get("_id").split(".")[0]

        try:
            # will throw KeyError if no list has been defined
            grouped_history_records[otuID].append(record)

        except KeyError:
            grouped_history_records[otuID] = []
            grouped_history_records[otuID].append(record)

    del history

    # ---------------------------------------------------------------------- #



    # ---------------------------------------------------------------------- #
    # we do a bunch of filtering

    # sort history record groups by otu version
    for key in grouped_history_records:
        grouped_history_records[key] = sorted(
            grouped_history_records[key], key=getComparableOrderKey
        )

    # filter only corrupted history records
    grouped_history_records = {
        key: value
        for (key, value) in grouped_history_records.items()
        if historyIsCorrupted(value)
    }

    # expand records into list that allocates space for missing records
    grouped_history_records = {
        key: expandRecordIDXByVersion(value)
        for (key, value) in grouped_history_records.items()
    }

    # filter only recoverable missing history records
    grouped_history_records = {
        key: value
        for (key, value) in grouped_history_records.items()
        if canBeRestored(value)
    }

    # ---------------------------------------------------------------------- #

    pass

    reconstructRecordFromDiff(grouped_history_records["c1f82472"][4])