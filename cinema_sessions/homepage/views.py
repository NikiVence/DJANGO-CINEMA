from django.shortcuts import render
from sessions import db
from sessions.views import database_page


@database_page
def home(request):
    return render(request, "homepage/home.html", {
        "total": db.get_count(), "sessions": db.get_sessions(limit=3),
    })
