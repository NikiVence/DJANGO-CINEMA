import io
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse

from . import db


class CinemaTestCase(SimpleTestCase):
    """Isolated sqlite3 fixture: tests never modify the delivered demonstration DB."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "sessions.db"
        self.override = override_settings(CINEMA_DB_PATH=self.path, DEBUG=False)
        self.override.enable()
        self.addCleanup(self.override.disable)
        call_command("init_db", stdout=io.StringIO())

    def execute(self, sql, parameters=()):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            cursor = connection.execute(sql, parameters)
            result = cursor.fetchall()
            connection.commit()
            return result


class SessionTests(CinemaTestCase):
    def test_seed_and_foreign_keys(self):
        self.assertEqual(len(db.get_halls()), 4)
        self.assertEqual(db.get_count(), 8)
        self.assertEqual(self.execute("PRAGMA foreign_key_check"), [])
        self.assertEqual(self.execute("PRAGMA integrity_check"), [("ok",)])
        with self.assertRaises(sqlite3.IntegrityError):
            self.execute("UPDATE sessions SET hall_id=999 WHERE id=1")

    def test_initialization_preserves_existing_records(self):
        self.execute("UPDATE sessions SET tickets=112 WHERE id=1")
        call_command("init_db", stdout=io.StringIO())
        self.assertEqual(db.get_count(), 8)
        self.assertEqual(db.get_session("matrix-classic")["tickets"], 112)

    def test_filter_results_match_direct_sql_and_html(self):
        for minimum in (50, 100):
            with self.subTest(minimum=minimum):
                response = self.client.get(reverse("sessions:list"), {"tickets": minimum})
                expected = self.execute(
                    "SELECT id FROM sessions WHERE tickets >= ? ORDER BY show_date, id",
                    (minimum,),
                )
                self.assertEqual([row["id"] for row in response.context["sessions"]],
                                 [row[0] for row in expected])
                for row in response.context["sessions"]:
                    self.assertContains(response, reverse("sessions:detail", args=[row["slug"]]))
        self.assertEqual(len(db.get_sessions(tickets=50)), 5)
        self.assertEqual(len(db.get_sessions(tickets=100)), 3)

    def test_order_and_limit_are_applied_in_database(self):
        for sort, order in (("date", "show_date ASC"), ("-date", "show_date DESC"),
                            ("tickets", "tickets ASC"), ("-tickets", "tickets DESC")):
            with self.subTest(sort=sort):
                response = self.client.get("/sessions/", {"sort": sort, "limit": 2})
                expected = self.execute(f"SELECT id FROM sessions ORDER BY {order}, id LIMIT 2")
                self.assertEqual([row["id"] for row in response.context["sessions"]],
                                 [row[0] for row in expected])

    def test_empty_filter_and_empty_database(self):
        response = self.client.get("/sessions/", {"tickets": 9999})
        self.assertContains(response, "Сеансы не найдены")
        self.execute("DELETE FROM sessions")
        self.execute("DELETE FROM halls")
        self.assertContains(self.client.get("/sessions/"), "Сеансы не найдены")
        self.assertContains(self.client.get("/halls/"), "Залы пока не добавлены")
        self.assertEqual(self.client.get("/").context["total"], 0)

    def test_invalid_parameters_and_injection(self):
        for query in ({"tickets": "-1"}, {"tickets": "1 OR 1=1"}, {"tickets": "2.5"},
                      {"limit": "0"}, {"limit": "1001"}, {"limit": "-1"},
                      {"tickets": "9" * 100}, {"sort": "tickets; DROP TABLE sessions;--"}):
            with self.subTest(query=query):
                response = self.client.get("/sessions/", query)
                self.assertContains(response, "Проверьте параметры", status_code=400)
        self.assertEqual(db.get_count(), 8)
        self.assertIsNone(db.get_session("' OR 1=1 --"))
        self.assertEqual(self.client.get("/sessions/?tickets=&limit=").status_code, 200)

    def test_detail_join_date_and_all_statuses(self):
        for slug, status in (("matrix-classic", "Билеты в продаже"),
                             ("interstellar", "Идёт показ"),
                             ("spirited-away", "Показ состоялся")):
            response = self.client.get(reverse("sessions:detail", args=[slug]))
            self.assertContains(response, status)
            self.assertContains(response, "20.10.2026")
            self.assertContains(response, db.get_session(slug)["hall_name"])
            self.assertContains(response, "Вместимость")
        response = self.client.get("/sessions/matrix-classic/")
        self.assertContains(response, "136 мин")
        self.assertContains(response, "19:00")
        self.assertContains(response, "data-toggle")

    def test_404_and_reserved_statistics_route(self):
        self.assertEqual(resolve("/sessions/statistics/").url_name, "statistics")
        for path in ("/sessions/not-a-movie/", "/missing-page/"):
            self.assertContains(self.client.get(path), "Страница или сеанс не найдены", status_code=404)

    def test_statistics_having_and_live_insert(self):
        response = self.client.get("/sessions/statistics/", {"minimum": 3})
        self.assertEqual([(r["show_type"], r["session_count"]) for r in response.context["statistics"]],
                         [("вечерний", 4)])
        self.execute("""INSERT INTO sessions
            (title, slug, show_type, show_date, duration, tickets, status, hall_id)
            VALUES ('Новый показ', 'new-show', 'утренний', '2026-10-23 10:00:00',
                    90, 12, 'запланирован', 1)""")
        response = self.client.get("/sessions/statistics/?minimum=3")
        self.assertContains(response, "Утренний")
        self.assertEqual(len(response.context["statistics"]), 2)
        self.assertEqual(self.client.get("/").context["total"], 9)
        self.assertContains(self.client.get("/sessions/statistics/?minimum=100"), "Нет типов сеансов")
        self.assertEqual(self.client.get("/sessions/statistics/?minimum=bad").status_code, 400)

    def test_sql_file_queries_are_all_executed(self):
        with patch.object(db, "fetch", wraps=db.fetch) as fetch:
            for url in ("/", "/halls/", "/sessions/", "/sessions/matrix-classic/", "/sessions/statistics/"):
                self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual({call.args[0] for call in fetch.call_args_list}, set(db.QUERIES))

    def test_database_failure_pages_do_not_leak_details(self):
        self.path.unlink()
        for url in ("/", "/halls/", "/sessions/", "/sessions/matrix-classic/", "/sessions/statistics/"):
            with self.subTest(url=url), self.assertLogs("sessions.views", level="ERROR"):
                response = self.client.get(url)
                self.assertContains(response, "Данные временно недоступны", status_code=503)
                self.assertNotContains(response, "Traceback", status_code=503)
                self.assertNotContains(response, str(self.path), status_code=503)
        self.assertFalse(self.path.exists())

    def test_malformed_date_is_handled(self):
        self.execute("UPDATE sessions SET show_date='bad-date' WHERE id=1")
        with self.assertLogs("sessions.views", level="ERROR"):
            self.assertEqual(self.client.get("/sessions/").status_code, 503)

    def test_session_update_is_visible_without_restart(self):
        self.execute("UPDATE sessions SET tickets=117 WHERE id=1")
        response = self.client.get("/sessions/matrix-classic/")
        self.assertContains(response, "117")
        self.assertEqual(response.context["session"]["tickets"], 117)
