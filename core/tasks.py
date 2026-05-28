from celery import shared_task

from core.services.ingestion_service import process_ingestion_job


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_ingestion_job_task(self, job_id: int):
    process_ingestion_job(job_id)
    return {"job_id": job_id, "status": "DONE"}

