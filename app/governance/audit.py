"""Secret redaction helpers used before audit and telemetry export."""

import re
from typing import Any

SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|password|secret|token)(['\"\s:=]+)([^\s,'\"}]+)"
)


def mask_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***REDACTED***"
            if any(
                term in key.casefold()
                for term in ("key", "token", "secret", "password", "authorization")
            )
            else mask_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [mask_secrets(item) for item in value]
    if isinstance(value, str):
        return SECRET_PATTERN.sub(r"\1\2***REDACTED***", value)
    return value
