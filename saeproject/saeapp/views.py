import csv
from datetime import datetime

from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .models import SensorName
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
    custom_names = _sensor_name_map()

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
                sensor_id = row["capteur_Id"]
                display_name = custom_names.get((house_id, sensor_id), row["piece"])
                rows.append(
                    {
                        "maison_id": house_id,
                        "maison": house_label,
                        "Id": sensor_id,
                        "capteur_Id": sensor_id,
                        "piece": row["piece"],
                        "display_name": display_name,
                        "date": row["date"],
                        "heure": row["heure"],
                        "temp": row["temp"],
                    }
                )
        except DatabaseError:
            continue

    return rows


def _sensor_name_map():
    try:
        return {
            (name.house_id, name.capteur_Id): name.display_name
            for name in SensorName.objects.all()
        }
    except DatabaseError:
        return {}


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
            if (
                sensor_lower in row["Id"].lower()
                or sensor_lower in row["piece"].lower()
                or sensor_lower in row["display_name"].lower()
            )
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
                "display_name": row["display_name"],
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
            "display_name": values["display_name"],
            "average": round(values["total"] / values["count"], 1),
            "count": values["count"],
        }
        for values in grouped.values()
    ]


def _sensor_editor_rows(rows):
    sensors = {}
    for row in rows:
        key = (row["maison_id"], row["Id"])
        sensors.setdefault(
            key,
            {
                "maison_id": row["maison_id"],
                "maison": row["maison"],
                "sensor": row["Id"],
                "piece": row["piece"],
                "display_name": row["display_name"],
            },
        )
    return list(sensors.values())


def index(request):
    rows = _filtered_rows(request)
    average_by_sensor = _average_by_sensor(rows)
    refresh_seconds = request.GET.get("refresh", "30")

    context = {
        "rows": rows,
        "average_by_sensor": average_by_sensor,
        "sensor_editor_rows": _sensor_editor_rows(rows),
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


def rename_sensor(request):
    if request.method != "POST":
        return redirect("index")

    house_id = request.POST.get("house_id", "").strip()
    sensor_id = request.POST.get("sensor_id", "").strip()
    display_name = request.POST.get("display_name", "").strip()
    next_url = request.POST.get("next", "").strip() or reverse("index")
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = reverse("index")

    if not house_id or not sensor_id:
        return redirect(next_url)

    if display_name:
        SensorName.objects.update_or_create(
            house_id=house_id,
            capteur_Id=sensor_id,
            defaults={"display_name": display_name},
        )
    else:
        SensorName.objects.filter(house_id=house_id, capteur_Id=sensor_id).delete()

    return redirect(next_url)


def export_csv(request):
    rows = _filtered_rows(request)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="temperatures.csv"'

    writer = csv.writer(response)
    writer.writerow(["maison", "capteur", "nom", "piece", "date", "heure", "temperature"])
    for row in rows:
        writer.writerow(
            [
                row["maison"],
                row["Id"],
                row["display_name"],
                row["piece"],
                row["date"],
                row["heure"],
                row["temp"],
            ]
        )

    return response
