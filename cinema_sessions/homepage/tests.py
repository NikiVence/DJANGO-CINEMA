from django.contrib.staticfiles import finders
from sessions.tests import CinemaTestCase


class HomepageTests(CinemaTestCase):
    def test_home_and_shared_navigation(self):
        response = self.client.get("/")
        self.assertContains(response, "Кинопоказы")
        self.assertEqual(response.context["total"], 8)
        for url in ("/halls/", "/sessions/", "/sessions/statistics/"):
            self.assertContains(response, f'href="{url}"')
        for asset in ("css/style.css", "js/main.js", "img/logo.svg", "img/logo.png"):
            self.assertIsNotNone(finders.find(asset))

    def test_all_main_pages_extend_base(self):
        for url in ("/", "/halls/", "/sessions/", "/sessions/matrix-classic/", "/sessions/statistics/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, "base.html")
