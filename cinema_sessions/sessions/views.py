import logging
import sqlite3
from functools import wraps

from django.http import Http404
from django.shortcuts import render

from . import db

logger = logging.getLogger(__name__)


def database_page(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except sqlite3.Error:
            logger.exception("Cannot read cinema database")
            return render(request, "database_error.html", status=503)
    return wrapped


def integer_parameter(request, name, default, minimum, maximum, errors):
    raw = request.GET.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
        if not minimum <= value <= maximum:
            raise ValueError
        return value
    except ValueError:
        errors.append(f"Параметр «{name}»: введите целое число от {minimum} до {maximum}.")
        return default


@database_page
def session_list(request):
    errors = []
    tickets = integer_parameter(request, "tickets", 0, 0, 2147483647, errors)
    limit = integer_parameter(request, "limit", -1, 1, 1000, errors)
    sort = request.GET.get("sort", "date")
    if sort not in db.SORT_OPTIONS:
        errors.append("Неизвестная сортировка. Выберите вариант из списка.")
        sort = "date"
    context = {
        "sessions": db.get_sessions(tickets, sort, limit),
        "tickets": tickets, "limit": "" if limit == -1 else limit,
        "sort": sort, "sort_options": db.SORT_OPTIONS.items(), "errors": errors,
    }
    return render(request, "sessions/session_list.html", context, status=400 if errors else 200)


@database_page
def session_detail(request, slug):
    session = db.get_session(slug)
    if session is None:
        raise Http404("Сеанс не найден")
    return render(request, "sessions/session_detail.html", {"session": session})


@database_page
def statistics(request):
    errors = []
    minimum = integer_parameter(request, "minimum", 2, 1, 1000, errors)
    return render(request, "sessions/statistics.html", {
        "statistics": db.get_statistics(minimum), "minimum": minimum,
        "total": db.get_count(), "errors": errors,
    }, status=400 if errors else 200)


def not_found(request, exception):
    return render(request, "404.html", status=404)
