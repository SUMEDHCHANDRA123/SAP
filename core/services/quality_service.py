from collections import Counter

from core.models import DataQualitySnapshot, IngestionJob


def score_job_quality(job: IngestionJob, errors: list[dict], total_rows: int) -> DataQualitySnapshot:
    """Compute a simple quality score and persist snapshot."""
    failed_rows = len(errors)
    valid_rows = max(total_rows - failed_rows, 0)
    score = round((valid_rows / total_rows) * 100, 2) if total_rows else 0

    issue_counts = Counter(err.get("reason", "Unknown") for err in errors)
    snapshot, _ = DataQualitySnapshot.objects.update_or_create(
        job=job,
        defaults={
            "tenant": job.tenant,
            "score": score,
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "flagged_rows": 0,
            "failed_rows": failed_rows,
            "issue_breakdown": dict(issue_counts),
        },
    )
    job.quality_score = snapshot.score
    job.quality_summary = snapshot.issue_breakdown
    job.save(update_fields=["quality_score", "quality_summary"])
    return snapshot

