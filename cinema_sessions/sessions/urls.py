from django.urls import path
from . import views

app_name = "sessions"
urlpatterns = [
    path("", views.session_list, name="list"),
    path("statistics/", views.statistics, name="statistics"),
    path("<slug:slug>/", views.session_detail, name="detail"),
]
