"""Provider-neutral structured model interface and retry policy."""

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

ResponseT = TypeVar("ResponseT", bound=BaseModel)


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0


class ModelUnavailableError(RuntimeError):
    """The configured model cannot be reached."""


class PolicyViolationError(RuntimeError):
    """A request violates a non-retryable safety policy."""


class StructuredOutputError(RuntimeError):
    """A model response remained invalid after one repair attempt."""


class ModelProvider(Protocol):
    name: str
    model_name: str
    last_usage: Usage

    async def generate(
        self, messages: list[Message], response_model: type[ResponseT]
    ) -> ResponseT: ...


def validate_structured[StructuredT: BaseModel](
    data: dict[str, Any], model: type[StructuredT]
) -> StructuredT:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise StructuredOutputError(str(exc)) from exc
