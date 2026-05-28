import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation


UNIT_MAP = {
    "L": "liters",
    "KG": "kg",
    "M3": "cubic_meters",
    "EA": "each",
}

PLANT_LOOKUP = {
    "PL01": "Mumbai Plant",
    "PL02": "Delhi Plant",
    "PL03": "Chennai Plant",
}

FIELD_ALIASES = {
    "EBELN": ["EBELN", "PO_NUMBER", "PURCHASE_ORDER"],
    "WERKS": ["WERKS", "PLANT", "Plant"],
    "MENGE": ["MENGE", "QUANTITY", "Quantity"],
    "MEINS": ["MEINS", "UNIT", "Unit"],
    "NETWR": ["NETWR", "AMOUNT", "Spend"],
    "WAERS": ["WAERS", "CURRENCY", "Currency"],
    "BLDAT": ["BLDAT", "POSTING_DATE", "PostingDate"],
}


def _pick(row: dict, logical_field: str) -> str:
    for key in FIELD_ALIASES.get(logical_field, [logical_field]):
        if key in row:
            return (row.get(key) or "").strip()
    return ""


def _parse_sap_date(value: str) -> str:
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except Exception:
            continue
    raise ValueError(f"Unparseable date '{value}'")


def parse_sap_procurement_csv(file_obj):
    """
    SAP procurement CSV parser (prototype).
    Expected typical procurement-style columns:
      EBELN, EBELP, WERKS, MATNR, MENGE, MEINS, NETWR, WAERS, BLDAT, LIFNR, BKTXT

    - Dates: BLDAT supports DD.MM.YYYY (common SAP export)
    - Units: MEINS normalized using UNIT_MAP when possible
    - Scope: Scope 3 (purchased goods/services)
    """
    reader = csv.DictReader(
        (line.decode("utf-8") if isinstance(line, (bytes, bytearray)) else line)
        for line in file_obj
    )
    records = []
    errors = []

    for row_number, row in enumerate(reader, start=2):
        menge_raw = _pick(row, "MENGE")
        meins_raw = _pick(row, "MEINS").upper()
        bldat_raw = _pick(row, "BLDAT")
        netwr_raw = _pick(row, "NETWR")
        waers_raw = _pick(row, "WAERS")
        werks_raw = _pick(row, "WERKS").upper()

        if not menge_raw and not netwr_raw:
            errors.append({"row_number": row_number, "reason": "Missing MENGE and NETWR"})
            continue

        if bldat_raw:
            try:
                bldat_iso = _parse_sap_date(bldat_raw)
            except Exception as exc:
                errors.append({"row_number": row_number, "reason": str(exc)})
                continue
        else:
            bldat_iso = None

        activity_unit = UNIT_MAP.get(meins_raw, meins_raw or "unknown")

        # Prefer quantity if present, else fallback to spend
        try:
            if menge_raw:
                activity_value = Decimal(menge_raw)
                activity_unit_out = activity_unit
            else:
                activity_value = Decimal(netwr_raw)
                activity_unit_out = waers_raw or "currency"
        except (InvalidOperation, ValueError):
            errors.append({"row_number": row_number, "reason": "Invalid numeric value"})
            continue

        row_out = dict(row)
        if bldat_iso:
            row_out["BLDAT"] = bldat_iso
        row_out["plant_code"] = werks_raw
        row_out["plant_name"] = PLANT_LOOKUP.get(werks_raw, "")

        records.append(
            {
                "source_type": "SAP_PROCUREMENT",
                "scope": "SCOPE_3",
                "activity_value": activity_value,
                "activity_unit": activity_unit_out,
                "normalized_value": None,
                "raw_data": row_out,
                "status": "PENDING",
            }
        )

    return {"records": records, "errors": errors}

