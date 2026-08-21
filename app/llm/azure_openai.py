"""Azure OpenAI adapter built on the OpenAI-compatible contract."""

from app.llm.openai_provider import OpenAIProvider


class AzureOpenAIProvider(OpenAIProvider):
    name = "azure_openai"

    def __init__(self, deployment: str, endpoint: str, api_key: str, api_version: str) -> None:
        try:
            from openai import AsyncAzureOpenAI  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install the 'providers' extra to use Azure OpenAI") from exc
        self.client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        self.model_name = deployment
        from app.llm.provider import Usage

        self.last_usage = Usage()
