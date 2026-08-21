"""Optional Anthropic structured-output adapter."""

import json
from typing import Any

from app.llm.provider import Message, ModelUnavailableError, ResponseT, Usage, validate_structured


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model_name: str, api_key: str | None = None) -> None:
        try:
            from anthropic import AsyncAnthropic  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install the 'providers' extra to use Anthropic") from exc
        self.client = AsyncAnthropic(api_key=api_key)
        self.model_name = model_name
        self.last_usage = Usage()

    async def generate(self, messages: list[Message], response_model: type[ResponseT]) -> ResponseT:
        system = f"Return only JSON matching this schema: {response_model.model_json_schema()}"
        try:
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                temperature=0,
                system=system,
                messages=[
                    {"role": m.role, "content": m.content} for m in messages if m.role != "system"
                ],
            )
        except Exception as exc:
            raise ModelUnavailableError(str(exc)) from exc
        self.last_usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        block = response.content[0]
        raw = getattr(block, "text", "{}")
        data: dict[str, Any] = json.loads(raw)
        return validate_structured(data, response_model)
