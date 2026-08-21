"""Approval and override governance that preserves original decisions."""

from app.models import ApprovalDecision, ApprovalRecord, ReleaseDecision


def automation_approval(
    workflow_id: str,
    approver: str,
    artifact_hash: str,
    approved: bool,
    comment: str,
) -> ApprovalRecord:
    if not artifact_hash:
        raise ValueError("artifact hash is required")
    if not comment.strip():
        raise ValueError("approval comment is required")
    return ApprovalRecord(
        workflow_id=workflow_id,
        stage="AUTOMATION",
        decision=ApprovalDecision.APPROVED if approved else ApprovalDecision.REJECTED,
        approver=approver,
        comment=comment,
        artifact_hash=artifact_hash,
    )


def release_override(
    workflow_id: str,
    approver: str,
    original: ReleaseDecision,
    override: ReleaseDecision,
    reason: str,
) -> ApprovalRecord:
    if original == override:
        raise ValueError("override must change the original decision")
    if len(reason.strip()) < 10:
        raise ValueError("a meaningful override reason is required")
    return ApprovalRecord(
        workflow_id=workflow_id,
        stage="RELEASE_OVERRIDE",
        decision=ApprovalDecision.APPROVED,
        approver=approver,
        comment=reason,
        artifact_hash="release-decision",
        original_decision=original.value,
        override_decision=override.value,
    )
