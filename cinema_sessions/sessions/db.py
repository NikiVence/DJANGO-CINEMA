"""The only data access layer: named SQL queries, sqlite3 and plain dictionaries."""
import re
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from django.conf import settings

SORT_OPTIONS = {
    "date": "Сначала ранние",
    "-date": "Сначала поздние",
    "tickets": "Билеты: по возрастанию",
    "-tickets": "Билеты: по убыванию",
}


def load_queries():
    source = (settings.BASE_DIR / "sql" / "queries.sql").read_text(encoding="utf-8")
    parts = re.split(r"^-- name: (\w+)\s*$", source, flags=re.MULTILINE)
    return dict(zip(parts[1::2], parts[2::2]))


QUERIES = load_queries()


def fetch(name, parameters=None):
    # mode=ro prevents silently creating an empty DB when its file is missing.
    uri = Path(settings.CINEMA_DB_PATH).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute(QUERIES[name], parameters or {})]
    for row in rows:
        if "show_date" in row:
            try:
                row["show_date"] = datetime.fromisoformat(row["show_date"])
            except (ValueError, TypeError) as error:
                raise sqlite3.DataError("Invalid session date") from error
    return rows


def get_sessions(tickets=0, sort="date", limit=-1):
    if sort not in SORT_OPTIONS:
        raise ValueError("Unsupported sort")
    return fetch("session_list", {"tickets": tickets, "sort": sort, "limit": limit})


def get_session(slug):
    rows = fetch("session_detail", {"slug": slug})
    return rows[0] if rows else None


def get_halls():
    return fetch("halls")


def get_count():
    return fetch("count")[0]["total"]


def get_statistics(minimum=2):
    return fetch("statistics", {"minimum": minimum})
