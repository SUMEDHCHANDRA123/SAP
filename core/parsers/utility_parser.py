import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation


def _parse_date(value: str) -> str:
    """Parse YYYY-MM-DD to ISO date string."""
    return datetime.strptime(value, "%Y-%m-%d").date().isoformat()


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _next_month_start(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


def _prorate_monthly_consumption(start: date, end: date, total_kwh: Decimal):
    """Split total consumption across months proportionally by days."""
    # Treat end as inclusive for day counting.
    total_days = (end - start).days + 1
    if total_days <= 0:
        return []

    segments = []
    cursor = start
    while cursor <= end:
        seg_start = cursor
        seg_end = min(end, _next_month_start(cursor) - timedelta(days=1))
        seg_days = (seg_end - seg_start).days + 1
        frac = Decimal(seg_days) / Decimal(total_days)
        seg_kwh = (total_kwh * frac).quantize(Decimal("0.0001"))
        segments.append((seg_start, seg_end, seg_days, seg_kwh, frac))
        cursor = seg_end + timedelta(days=1)
    return segments


def parse_utility_electricity_csv(file_obj):
    """
    Parse utility electricity CSV into emission record dicts.
    - Validates that consumption_kwh is present and > 0.
    - Stores billing period dates in raw_data as ISO strings.
    """
    reader = csv.DictReader(
        (line.decode("utf-8") if isinstance(line, (bytes, bytearray)) else line)
        for line in file_obj
    )
    records: list[dict] = []
    errors: list[dict] = []

    for row_number, row in enumerate(reader, start=2):
        consumption_raw = (row.get("consumption_kwh") or "").strip()
        unit_raw = (row.get("unit") or row.get("uom") or "kwh").strip().lower()
        tariff_raw = (row.get("tariff_type") or row.get("tariff") or "").strip()

        if not consumption_raw:
            errors.append(
                {"row_number": row_number, "reason": "consumption_kwh is blank"}
            )
            continue

        if unit_raw not in {"kwh", "kilowatt_hour", "kilowatt-hours"}:
            errors.append(
                {"row_number": row_number, "reason": f"Unsupported electricity unit '{unit_raw}'"}
            )
            continue

        try:
            consumption = Decimal(consumption_raw)
        except (InvalidOperation, ValueError):
            errors.append(
                {
                    "row_number": row_number,
                    "reason": f"Invalid consumption_kwh '{consumption_raw}'",
                }
            )
            continue

        if consumption <= 0:
            errors.append(
                {"row_number": row_number, "reason": "consumption_kwh is zero"}
            )
            continue

        row_out = dict(row)
        try:
            start_iso = _parse_date((row.get("billing_period_start") or "").strip())
            end_iso = _parse_date((row.get("billing_period_end") or "").strip())
            row_out["billing_period_start"] = start_iso
            row_out["billing_period_end"] = end_iso
        except Exception as e:
            errors.append(
                {
                    "row_number": row_number,
                    "reason": f"Invalid billing period dates: {e}",
                }
            )
            continue

        start_dt = datetime.strptime(start_iso, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_iso, "%Y-%m-%d").date()
        segments = _prorate_monthly_consumption(start_dt, end_dt, consumption)
        if not segments:
            errors.append({"row_number": row_number, "reason": "Invalid billing period range"})
            continue

        # Create one record per month segment to align with realistic billing periods.
        for seg_start, seg_end, seg_days, seg_kwh, frac in segments:
            seg_raw = dict(row_out)
            seg_raw["allocation_start"] = seg_start.isoformat()
            seg_raw["allocation_end"] = seg_end.isoformat()
            seg_raw["allocation_days"] = seg_days
            seg_raw["allocation_fraction"] = str(frac)
            seg_raw["tariff_type"] = tariff_raw or "unknown"
            records.append(
                {
                    "source_type": "UTILITY_ELECTRICITY",
                    "scope": "SCOPE_2",
                    "activity_value": seg_kwh,
                    "activity_unit": "kwh",
                    "normalized_value": seg_kwh,
                    "raw_data": seg_raw,
                    "status": "PENDING",
                }
            )

    return {"records": records, "errors": errors}

