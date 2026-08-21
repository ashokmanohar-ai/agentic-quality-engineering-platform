"""Tool classification and fixed allow-list enforcement."""

from enum import StrEnum


class ToolCategory(StrEnum):
    READ_ONLY = "READ_ONLY"
    EXECUTION = "EXECUTION"
    WRITE = "WRITE"
    HIGH_IMPACT = "HIGH_IMPACT"


ALLOWED_COMMANDS: dict[str, tuple[str, ...]] = {
    "format_check": ("npm", "run", "format:check"),
    "lint": ("npm", "run", "lint"),
    "typecheck": ("npm", "run", "typecheck"),
    "discover": ("npm", "run", "test:discover"),
}


def command_for(action: str) -> tuple[str, ...]:
    try:
        return ALLOWED_COMMANDS[action]
    except KeyError as exc:
        raise PermissionError(f"command action is not allow-listed: {action}") from exc
