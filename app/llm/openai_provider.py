"""OpenAI-compatible structured-output adapter, loaded only when configured."""

import json
from typing import Any

from app.llm.provider import Message, ModelUnavailableError, ResponseT, Usage, validate_structured


class OpenAIProvider:
    name = "openai"

    def __init__(
        self, model_name: str, api_key: str | None = None, base_url: str | None = None
    ) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install the 'providers' extra to use OpenAI") from exc
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.last_usage = Usage()

    async def generate(self, messages: list[Message], response_model: type[ResponseT]) -> ResponseT:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                temperature=0,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise ModelUnavailableError(str(exc)) from exc
        usage = response.usage
        self.last_usage = Usage(
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
        content = response.choices[0].message.content or "{}"
        data: dict[str, Any] = json.loads(content)
        try:
            return validate_structured(data, response_model)
        except Exception:
            repair = messages + [
                Message("user", f"Repair the JSON to match: {response_model.model_json_schema()}")
            ]
            repaired = await self.client.chat.completions.create(
                model=self.model_name,
                temperature=0,
                messages=[{"role": m.role, "content": m.content} for m in repair],
                response_format={"type": "json_object"},
            )
            return validate_structured(
                json.loads(repaired.choices[0].message.content or "{}"), response_model
            )
