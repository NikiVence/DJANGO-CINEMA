import sqlite3
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the cinema SQLite database and insert missing demo records."

    def handle(self, *args, **options):
        path = Path(settings.CINEMA_DB_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(sqlite3.connect(path)) as connection:
                connection.executescript((settings.BASE_DIR / "sql/schema.sql").read_text(encoding="utf-8"))
                connection.executescript((settings.BASE_DIR / "sql/seed.sql").read_text(encoding="utf-8"))
        except sqlite3.Error as error:
            raise CommandError(f"Database initialization failed: {error}") from error
        self.stdout.write(self.style.SUCCESS(f"Database ready: {path}"))
