"""Status page shown at the backend's root URL (http://127.0.0.1:8000/)."""

from django.conf import settings
from django.db import connection
from django.shortcuts import render


def home(request):
    from placements.models import Appeal, Placement, PlacementRun, School, Student

    try:
        stats = {
            "students": Student.objects.count(),
            "schools": School.objects.count(),
            "placements": Placement.objects.count(),
            "runs": PlacementRun.objects.count(),
            "pending_appeals": Appeal.objects.filter(status="pending").count(),
        }
        db_ok, db_error = True, ""
    except Exception as exc:  # noqa: BLE001 -- e.g. migrations not applied yet
        stats, db_ok, db_error = {}, False, str(exc)

    db = settings.DATABASES["default"]
    engine = "SQLite" if "sqlite" in db["ENGINE"] else "PostgreSQL"
    db_name = str(db["NAME"]).replace("\\", "/").split("/")[-1]
    return render(request, "backend_home.html", {
        "stats": stats, "db_ok": db_ok, "db_error": db_error, "engine": engine, "db_name": db_name,
        "vendor": connection.vendor, "debug": settings.DEBUG,
    })
