"""Script used to create mongo indexes."""

import argparse

from pymongo import ASCENDING, DESCENDING, MongoClient

parser = argparse.ArgumentParser()

parser.add_argument("connection_uri", type=str, metavar="connection-uri")
parser.add_argument("database", type=str)
parser.add_argument("collection", type=str)

args = parser.parse_args()

client = MongoClient(args.connection_uri)

db = client.get_database(name=args.database)
collection = db.get_collection(name=args.collection)

collection.create_index(
    [("_source.statement.timestamp", ASCENDING), ("_id", ASCENDING)]
)
collection.create_index(
    [("_source.statement.timestamp", DESCENDING), ("_id", DESCENDING)]
)
collection.create_index("_source.metadata.voided")

for index in collection.list_indexes():
    print(dict(index).get("name")) # noqa: T201
