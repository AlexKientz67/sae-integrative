import csv
from datetime import datetime

from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import render

from .models import TemperatureDataM1
from .models import TemperatureDataM2


HOUSE_SOURCES = (
    ("1", "Maison 1", TemperatureDataM1),
    ("2", "Maison 2", TemperatureDataM2),
)
MAX_DISPLAYED_ROWS = 25


def _parse_date(value):
    if not value:
        return None

    for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    return None


def _format_input_date(value):
    parsed = _parse_date(value)
    return parsed.isoformat() if parsed else ""


def _row_date(row):
    return _parse_date(row["date"])


def _load_temperature_rows(house_filter=""):
    rows = []

    for house_id, house_label, model in HOUSE_SOURCES:
        if house_filter and house_filter != house_id:
            continue

        try:
            queryset = (
                model.objects.all()
                .order_by("date", "heure", "id")
                .values("capteur_Id", "piece", "date", "heure", "temp")
            )
            for row in queryset:
                rows.append(
                    {
                        "maison_id": house_id,
                        "maison": house_label,
                        "Id": row["capteur_Id"],
                        "capteur_Id": row["capteur_Id"],
                        "piece": row["piece"],
                        "date": row["date"],
                        "heure": row["heure"],
                        "temp": row["temp"],
                    }
                )
        except DatabaseError:
            continue

    return rows


def _filtered_rows(request):
    house = request.GET.get("house", "").strip()
    sensor = request.GET.get("sensor", "").strip()
    start = _parse_date(request.GET.get("start", ""))
    end = _parse_date(request.GET.get("end", ""))
    rows = _load_temperature_rows(house)

    if sensor:
        sensor_lower = sensor.lower()
        rows = [
            row
            for row in rows
            if sensor_lower in row["Id"].lower() or sensor_lower in row["piece"].lower()
        ]

    if start:
        rows = [row for row in rows if _row_date(row) and _row_date(row) >= start]

    if end:
        rows = [row for row in rows if _row_date(row) and _row_date(row) <= end]

    rows.sort(
        key=lambda row: (
            _row_date(row) or datetime.min.date(),
            row["heure"],
            row["maison_id"],
            row["Id"],
        ),
        reverse=True,
    )
    return rows[:MAX_DISPLAYED_ROWS]


def _average_by_sensor(rows):
    grouped = {}
    for row in rows:
        key = (row["maison_id"], row["Id"])
        grouped.setdefault(
            key,
            {
                "total": 0,
                "count": 0,
                "piece": row["piece"],
                "maison": row["maison"],
                "sensor": row["Id"],
            },
        )
        grouped[key]["total"] += float(row["temp"])
        grouped[key]["count"] += 1

    return [
        {
            "maison": values["maison"],
            "sensor": values["sensor"],
            "piece": values["piece"],
            "average": round(values["total"] / values["count"], 1),
            "count": values["count"],
        }
        for values in grouped.values()
    ]


def index(request):
    rows = _filtered_rows(request)
    average_by_sensor = _average_by_sensor(rows)
    refresh_seconds = request.GET.get("refresh", "30")

    context = {
        "rows": rows,
        "average_by_sensor": average_by_sensor,
        "global_average": round(sum(float(row["temp"]) for row in rows) / len(rows), 1) if rows else None,
        "houses": HOUSE_SOURCES,
        "house_filter": request.GET.get("house", "").strip(),
        "sensor_filter": request.GET.get("sensor", "").strip(),
        "start_filter": _format_input_date(request.GET.get("start", "")),
        "end_filter": _format_input_date(request.GET.get("end", "")),
        "auto_refresh": request.GET.get("auto_refresh") == "on",
        "refresh_seconds": refresh_seconds if refresh_seconds.isdigit() else "30",
        "total_count": len(rows),
    }
    return render(request, "saeapp/index.html", context)


def export_csv(request):
    rows = _filtered_rows(request)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="temperatures.csv"'

    writer = csv.writer(response)
    writer.writerow(["maison", "capteur", "piece", "date", "heure", "temperature"])
    for row in rows:
        writer.writerow([row["maison"], row["Id"], row["piece"], row["date"], row["heure"], row["temp"]])

    return response
