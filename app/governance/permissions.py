"""Role-based permission checks for protected operations."""

from app.models import Role

PERMISSIONS: dict[str, set[Role]] = {
    "read": {Role.VIEWER, Role.QUALITY_ENGINEER, Role.APPROVER, Role.ADMIN},
    "create_workflow": {Role.QUALITY_ENGINEER, Role.APPROVER, Role.ADMIN},
    "approve": {Role.APPROVER, Role.ADMIN},
    "execute": {Role.QUALITY_ENGINEER, Role.APPROVER, Role.ADMIN},
    "audit": {Role.APPROVER, Role.ADMIN},
    "configure": {Role.ADMIN},
}


def authorize(role: Role, action: str) -> None:
    if role not in PERMISSIONS.get(action, set()):
        raise PermissionError(f"role {role} cannot perform {action}")
