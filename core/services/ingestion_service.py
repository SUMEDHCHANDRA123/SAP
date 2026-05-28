from django.db import transaction
from django.utils import timezone

from core.models import EmissionRecord, IngestionJob
from core.parsers.sap_parser import parse_sap_fuel_csv
from core.parsers.sap_procurement_parser import parse_sap_procurement_csv
from core.parsers.utility_parser import parse_utility_electricity_csv
from core.parsers.travel_parser import parse_travel_concur_csv
from core.services.factor_engine import apply_factor
from core.services.quality_service import score_job_quality
from core.services.workflow_service import ensure_workflow, log_audit


PARSER_BY_SOURCE = {
    IngestionJob.SourceType.SAP_FUEL: parse_sap_fuel_csv,
    IngestionJob.SourceType.SAP_PROCUREMENT: parse_sap_procurement_csv,
    IngestionJob.SourceType.UTILITY_ELECTRICITY: parse_utility_electricity_csv,
    IngestionJob.SourceType.TRAVEL: parse_travel_concur_csv,
}


def process_ingestion_job(job_id: int) -> IngestionJob:
    job = IngestionJob.objects.select_related("tenant").get(pk=job_id)
    job.status = IngestionJob.Status.PROCESSING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    parser = PARSER_BY_SOURCE.get(job.source_type)
    if parser is None:
        job.status = IngestionJob.Status.FAILED
        job.error_log = [{"row_number": None, "reason": f"No parser for {job.source_type}"}]
        job.error_count = 1
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_log", "error_count", "completed_at"])
        return job

    if not job.uploaded_file:
        job.status = IngestionJob.Status.FAILED
        job.error_log = [{"row_number": None, "reason": "Uploaded file missing"}]
        job.error_count = 1
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_log", "error_count", "completed_at"])
        return job

    with job.uploaded_file.open("rb") as fh:
        result = parser(fh)

    records_data = result["records"]
    errors = result["errors"]
    total_rows = len(records_data) + len(errors)

    with transaction.atomic():
        objs = []
        for rd in records_data:
            record = EmissionRecord(
                tenant=job.tenant,
                job=job,
                source_type=rd["source_type"],
                scope=rd["scope"],
                activity_value=rd["activity_value"],
                activity_unit=rd["activity_unit"],
                normalized_value=rd.get("normalized_value"),
                raw_data=rd["raw_data"],
                status=rd.get("status", EmissionRecord.Status.PENDING),
                approval_stage="ANALYST_REVIEW",
            )
            record = apply_factor(record)
            objs.append(record)

        created = EmissionRecord.objects.bulk_create(objs, batch_size=1000)
        for record in created:
            ensure_workflow(record)

        job.status = IngestionJob.Status.DONE
        job.row_count = total_rows
        job.error_count = len(errors)
        job.error_log = errors
        job.completed_at = timezone.now()
        job.save(
            update_fields=[
                "status",
                "row_count",
                "error_count",
                "error_log",
                "completed_at",
            ]
        )
        score_job_quality(job, errors, total_rows)
        log_audit("ingestion_processed", job=job, payload={"rows": total_rows, "errors": len(errors)})

    return job

