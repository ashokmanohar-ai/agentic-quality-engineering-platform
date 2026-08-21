"""Structured logging helpers with secret masking."""

import json
import logging
from typing import Any

from app.governance.audit import mask_secrets

logger = logging.getLogger("agentic_qe")


def log_event(event: str, details: dict[str, Any]) -> None:
    logger.info(json.dumps({"event": event, "details": mask_secrets(details)}, default=str))
