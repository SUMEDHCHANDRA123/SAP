import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation


MEINS_MAP = {
    "L": "liters",
    "KG": "kg",
    "M3": "cubic_meters",
}

PLANT_LOOKUP = {
    "PL01": "Mumbai Plant",
    "PL02": "Delhi Plant",
    "PL03": "Chennai Plant",
}

FIELD_ALIASES = {
    "MENGE": ["MENGE", "Menge", "QUANTITY", "Quantity"],
    "MEINS": ["MEINS", "Meins", "UNIT", "Unit"],
    "BLDAT": ["BLDAT", "Bldat", "POSTING_DATE", "PostingDate", "BUDAT"],
    "WERKS": ["WERKS", "Werks", "PLANT", "Plant"],
}


def _pick(row: dict, logical_field: str) -> str:
    for key in FIELD_ALIASES.get(logical_field, [logical_field]):
        if key in row:
            return (row.get(key) or "").strip()
    return ""


def _parse_sap_date(value: str) -> str:
    # Common SAP export variants.
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except Exception:
            continue
    raise ValueError(f"Unparseable date '{value}'")


def parse_sap_fuel_csv(file_obj):
    """
    Parse SAP fuel CSV into normalized emission record dicts.
    - Validates quantity, unit, and posting date.
    - Converts BLDAT from DD.MM.YYYY to ISO date string.
    """
    reader = csv.DictReader(
        (line.decode("utf-8") if isinstance(line, (bytes, bytearray)) else line)
        for line in file_obj
    )
    records: list[dict] = []
    errors: list[dict] = []

    for row_number, row in enumerate(reader, start=2):
        menge_raw = _pick(row, "MENGE")
        meins_raw = _pick(row, "MEINS").upper()
        bldat_raw = _pick(row, "BLDAT")
        werks_raw = _pick(row, "WERKS").upper()

        if not menge_raw:
            errors.append({"row_number": row_number, "reason": "MENGE is blank"})
            continue

        if meins_raw not in MEINS_MAP:
            errors.append(
                {"row_number": row_number, "reason": f"Unrecognized MEINS '{meins_raw}'"}
            )
            continue

        try:
            bldat_iso = _parse_sap_date(bldat_raw)
        except Exception as exc:
            errors.append(
                {"row_number": row_number, "reason": str(exc)}
            )
            continue

        try:
            activity_value = Decimal(menge_raw)
        except (InvalidOperation, ValueError):
            errors.append(
                {"row_number": row_number, "reason": f"Invalid MENGE '{menge_raw}'"}
            )
            continue

        row_out = dict(row)
        row_out["BLDAT"] = bldat_iso
        row_out["plant_code"] = werks_raw
        row_out["plant_name"] = PLANT_LOOKUP.get(werks_raw, "")

        records.append(
            {
                "source_type": "SAP_FUEL",
                "scope": "SCOPE_1",
                "activity_value": activity_value,
                "activity_unit": MEINS_MAP[meins_raw],
                "normalized_value": None,
                "raw_data": row_out,
                "status": "PENDING",
            }
        )

    return {"records": records, "errors": errors}

