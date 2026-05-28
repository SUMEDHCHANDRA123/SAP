from django.utils import timezone

from core.models import (
    ApprovalDecision,
    ApprovalWorkflow,
    AuditEvent,
    EmissionRecord,
)


def ensure_workflow(record: EmissionRecord) -> ApprovalWorkflow:
    workflow, _ = ApprovalWorkflow.objects.get_or_create(
        record=record,
        defaults={"tenant": record.tenant, "current_stage": ApprovalWorkflow.Stage.ANALYST_REVIEW},
    )
    return workflow


def log_audit(event_type: str, record: EmissionRecord | None = None, payload: dict | None = None, actor=None, job=None) -> None:
    tenant = record.tenant if record else (job.tenant if job else None)
    if not tenant:
        return
    AuditEvent.objects.create(
        tenant=tenant,
        event_type=event_type,
        actor=actor,
        record=record,
        job=job,
        payload=payload or {},
    )


def apply_decision(record: EmissionRecord, decision: str, note: str = "", actor=None) -> EmissionRecord:
    workflow = ensure_workflow(record)
    ApprovalDecision.objects.create(
        workflow=workflow,
        stage=workflow.current_stage,
        decision=decision,
        note=note,
        decided_by=actor if getattr(actor, "is_authenticated", False) else None,
    )

    if decision == ApprovalDecision.Decision.APPROVED:
        if workflow.current_stage == ApprovalWorkflow.Stage.ANALYST_REVIEW:
            workflow.current_stage = ApprovalWorkflow.Stage.REVIEWER_REVIEW
            record.status = EmissionRecord.Status.PENDING
            record.approval_stage = workflow.current_stage
            record.is_locked = False
        elif workflow.current_stage == ApprovalWorkflow.Stage.REVIEWER_REVIEW:
            workflow.current_stage = ApprovalWorkflow.Stage.MANAGER_SIGNOFF
            record.status = EmissionRecord.Status.PENDING
            record.approval_stage = workflow.current_stage
            record.is_locked = False
        else:
            workflow.current_stage = ApprovalWorkflow.Stage.COMPLETED
            workflow.is_completed = True
            record.status = EmissionRecord.Status.APPROVED
            record.approval_stage = workflow.current_stage
            record.is_locked = True
    elif decision == ApprovalDecision.Decision.REJECTED:
        record.status = EmissionRecord.Status.REJECTED
        record.reject_note = note or ""
        record.is_locked = True
    else:
        record.status = EmissionRecord.Status.FLAGGED
        record.flag_reason = note or ""
        record.is_locked = False

    if getattr(actor, "is_authenticated", False):
        record.edited_by = actor

    record.save()
    workflow.save()
    log_audit(
        "record_decision",
        record=record,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        payload={"decision": decision, "stage": workflow.current_stage, "note": note, "at": timezone.now().isoformat()},
    )
    return record

