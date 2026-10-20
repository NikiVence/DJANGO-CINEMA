from sessions.tests import CinemaTestCase


class HallTests(CinemaTestCase):
    def test_hall_update_is_reflected_in_list_and_session(self):
        self.execute("UPDATE halls SET name=?, capacity=? WHERE id=1", ("Новый зал", 250))
        self.assertContains(self.client.get("/halls/"), "Новый зал")
        response = self.client.get("/sessions/matrix-classic/")
        self.assertContains(response, "Новый зал")
        self.assertContains(response, "250 мест")
