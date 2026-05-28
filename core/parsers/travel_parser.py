import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path


CATEGORY_MAP = {
    "Flight": "TRAVEL_FLIGHT",
    "Hotel": "TRAVEL_HOTEL",
    "Ground": "TRAVEL_GROUND",
}

_AIRPORTS = None


def _load_airports():
    global _AIRPORTS
    if _AIRPORTS is not None:
        return _AIRPORTS
    path = Path(__file__).resolve().parent / "airports.json"
    if not path.exists():
        _AIRPORTS = {}
        return _AIRPORTS
    _AIRPORTS = json.loads(path.read_text(encoding="utf-8"))
    return _AIRPORTS


def _haversine_km(lat1, lon1, lat2, lon2) -> Decimal:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return Decimal(str(r * c)).quantize(Decimal("0.0001"))


def _maybe_distance_from_iata(origin: str, destination: str) -> Decimal | None:
    airports = _load_airports()
    if not origin or not destination:
        return None
    o = airports.get(origin.upper())
    d = airports.get(destination.upper())
    if not o or not d:
        return None
    return _haversine_km(o["lat"], o["lon"], d["lat"], d["lon"])


def parse_travel_concur_csv(file_obj):
    """
    Parse travel CSV into emission record dicts.
    - Maps category to travel sub-type.
    - Requires distance_km for flight rows.
    - Treats all travel as Scope 3.
    """
    reader = csv.DictReader(
        (line.decode("utf-8") if isinstance(line, (bytes, bytearray)) else line)
        for line in file_obj
    )
    records: list[dict] = []
    errors: list[dict] = []

    for row_number, row in enumerate(reader, start=2):
        category = (row.get("category") or "").strip()
        travel_date_raw = (row.get("travel_date") or "").strip()

        if category not in CATEGORY_MAP:
            errors.append(
                {"row_number": row_number, "reason": f"Unrecognized category '{category}'"}
            )
            continue

        try:
            dt = datetime.strptime(travel_date_raw, "%Y-%m-%d").date()
        except Exception:
            errors.append(
                {
                    "row_number": row_number,
                    "reason": f"Unparseable travel_date '{travel_date_raw}'",
                }
            )
            continue

        distance_raw = (row.get("distance_km") or "").strip()
        activity_value = None
        activity_unit = None

        if category == "Flight":
            if distance_raw:
                try:
                    activity_value = Decimal(distance_raw)
                except (InvalidOperation, ValueError):
                    errors.append(
                        {
                            "row_number": row_number,
                            "reason": f"Invalid distance_km '{distance_raw}'",
                        }
                    )
                    continue
            else:
                origin = (row.get("origin") or "").strip()
                dest = (row.get("destination") or "").strip()
                inferred = _maybe_distance_from_iata(origin, dest)
                if inferred is None:
                    errors.append(
                        {
                            "row_number": row_number,
                            "reason": "Flight row missing distance_km and route not resolvable",
                        }
                    )
                    continue
                activity_value = inferred
                row["distance_km"] = str(inferred)
            activity_unit = "km"
        elif category == "Hotel":
            nights_raw = (row.get("nights") or "").strip() or "0"
            try:
                activity_value = Decimal(nights_raw)
            except (InvalidOperation, ValueError):
                errors.append(
                    {"row_number": row_number, "reason": f"Invalid nights '{nights_raw}'"}
                )
                continue
            activity_unit = "nights"
        else:
            cost_raw = (row.get("cost_usd") or "").strip() or "0"
            try:
                activity_value = Decimal(cost_raw)
            except (InvalidOperation, ValueError):
                errors.append(
                    {"row_number": row_number, "reason": f"Invalid cost_usd '{cost_raw}'"}
                )
                continue
            activity_unit = "usd"

        row_out = dict(row)
        row_out["travel_date"] = dt.isoformat()

        records.append(
            {
                "source_type": CATEGORY_MAP[category],
                "scope": "SCOPE_3",
                "activity_value": activity_value,
                "activity_unit": activity_unit,
                "normalized_value": None,
                "raw_data": row_out,
                "status": "PENDING",
            }
        )

    return {"records": records, "errors": errors}

