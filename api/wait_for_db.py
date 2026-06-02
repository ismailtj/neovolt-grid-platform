import os
import time

import psycopg2
from psycopg2 import OperationalError


def wait_for_db() -> None:
    host = os.environ.get("POSTGRES_HOST", "database")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    dbname = os.environ["POSTGRES_DB"]

    while True:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
                connect_timeout=3,
            )
            conn.close()
            print("Database is ready.")
            break
        except OperationalError as exc:
            print(f"Database not ready, retrying: {exc}")
            time.sleep(2)


if __name__ == "__main__":
    wait_for_db()
