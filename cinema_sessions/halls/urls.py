from django.urls import path
from .views import hall_list

app_name = "halls"
urlpatterns = [path("", hall_list, name="list")]
