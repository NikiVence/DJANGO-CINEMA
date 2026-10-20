from django.urls import include, path

urlpatterns = [
    path("", include("homepage.urls")),
    path("halls/", include("halls.urls")),
    path("sessions/", include("sessions.urls")),
]
handler404 = "sessions.views.not_found"
