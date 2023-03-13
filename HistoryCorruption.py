import pymongo
from pymongo import MongoClient


class UncorruptedCollection(Exception):
    pass


class EmptyHistoryRecords(Exception):
    pass


def canBeSimplyRestored(records: list = []) -> bool:
    """
    Determines if a corrupted collection of otu history records can be simply restored

        Parameters:
            records (list): the collection of otu history records

        Returns:
            False: The collection contains multiple corrupted records
            True: The collection contains only 1 corrupted records
    """
    corruption_level = sum(map(lambda record: record is None, records))

    if corruption_level == 0:
        raise UncorruptedCollection()
    
    else:
        return True if (corruption_level == 1) else False


def canRestoreCollection(records: list = []) -> bool:
    """
    Determines if a corrupted collection of otu history records can be restored

        Parameters:
            records (list): the collection of otu history records

        Returns:
            False: The length of the collection is zero, or all elements in the collection are None
            True: The collection contains atleast 1 non-None entry 

        Raises:
            EmptyHistoryRecords: parameter "records" is None
    """
    if records is None:
        raise EmptyHistoryRecords()
    
    elif len(records) == 0:
        return False
    
    else:
        return False if (len(records) == sum(map(lambda record: record is None, records))) else True
        



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

    history_collections: dict = {}

    # organize history records by otu id
    for record in list(history.find()):
        otuID = record.get("_id").split(".")[0]

        try:
            history_collections[otuID].append(record)

        # define a new collection of history records if one does not exist at the current otuID
        except KeyError:
            history_collections[otuID] = [record]

    del history

    # ---------------------------------------------------------------------- #



    # ---------------------------------------------------------------------- #
    # we do a bunch of filtering

    # sort history records into collections by otu id
    for key in history_collections:
        history_collections[key] = sorted(
            history_collections[key], key=getComparableOrderKey
        )

    # filter only corrupted history collections
    history_collections = {
        key: value
        for (key, value) in history_collections.items()
        if historyIsCorrupted(value)
    }

    # expand records into list that allocates space for missing records
    history_collections = {
        key: expandRecordIDXByVersion(value)
        for (key, value) in history_collections.items()
    }

    # filter only restorable collections
    restorable_corrupted_history_collections: dict = {
        key: value
        for (key, value) in history_collections.items()
        if canRestoreCollection(value)
    }

    del history_collections

    simple_corrupted_history_collections: dict = dict()
    complex_corrupted_history_collections: dict = dict()
    
    for (key, value) in restorable_corrupted_history_collections.items():
        if canBeSimplyRestored(value):
            simple_corrupted_history_collections.update({key: value})
        
        else:
            complex_corrupted_history_collections.update({key: value})

    del restorable_corrupted_history_collections

    # ---------------------------------------------------------------------- #

    pass