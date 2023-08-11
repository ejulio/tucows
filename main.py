import sys
from argparse import ArgumentParser, Namespace
import psycopg
from psycopg.connection import Connection

from typing import Callable

from tucows.query import query

def main():
    args = parse_args()

    if args.query:
        query(lazy_connection(args.db_connection))
    elif args.add:
        add(lazy_connection(args.db_connection))
    else:
        raise ValueError("You must specify --query or --add")

def parse_args() -> Namespace:
    ap = ArgumentParser()

    ap.add_argument(
        "--query",
        "-q",
        required=False,
        action="store_true",
        help="Queries the database with the given query from stdin",
    )

    ap.add_argument(
        "--add",
        "-a",
        required=False,
        type=str,
        help="Downloads the given file, parses and inserts the graph in the database",
    )

    ap.add_argument(
        "--db-connection",
        required=True,
        type=str,
        help="Database connection string in the form postgresql://user:secret@localhost/dbname. See https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING"
    )

    return ap.parse_args()


def lazy_connection(connection_string: str) -> Callable[[], Connection]:
    """Returns a function to connect with the database with the given connection string"""
    return lambda: psycopg.connect(connection_string)



def add(connect_db: Callable[[], Connection]):
    print("add")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("error running main:", e)
        sys.exit(1)