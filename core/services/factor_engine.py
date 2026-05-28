from decimal import Decimal

from core.models import EmissionFactor, EmissionRecord


def resolve_factor(record: EmissionRecord) -> EmissionFactor | None:
    """Resolve emission factor using tenant > global precedence."""
    candidates = EmissionFactor.objects.filter(
        is_active=True,
        input_unit=record.activity_unit,
        source_type__in=["", record.source_type],
        scope__in=["", record.scope],
    ).filter(year__lte=record.created_at.year)

    tenant_candidates = candidates.filter(tenant=record.tenant).order_by("-year", "-updated_at")
    if tenant_candidates.exists():
        return tenant_candidates.first()

    global_candidates = candidates.filter(tenant__isnull=True).order_by("-year", "-updated_at")
    if global_candidates.exists():
        return global_candidates.first()
    return None


def apply_factor(record: EmissionRecord) -> EmissionRecord:
    """Apply a factor and persist calculation trace."""
    factor = resolve_factor(record)
    if not factor:
        return record

    co2e_kg = Decimal(record.activity_value) * Decimal(factor.value)
    record.co2e_kg = co2e_kg
    record.factor_value = factor.value
    record.factor_unit = factor.input_unit
    record.factor_version = factor.version
    record.factor_source = factor.source_name
    record.factor_region = factor.region
    record.factor_year = factor.year
    record.calc_trace = {
        "formula": "activity_value * factor_value",
        "activity_value": str(record.activity_value),
        "factor_value": str(factor.value),
        "input_unit": factor.input_unit,
        "output_unit": factor.output_unit,
        "co2e_kg": str(co2e_kg),
        "factor_id": factor.id,
    }
    return record

