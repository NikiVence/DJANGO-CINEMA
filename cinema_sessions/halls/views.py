from django.shortcuts import render
from sessions import db
from sessions.views import database_page


@database_page
def hall_list(request):
    return render(request, "halls/hall_list.html", {"halls": db.get_halls()})
