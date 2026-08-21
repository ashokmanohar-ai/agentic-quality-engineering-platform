"""Provider selection without coupling core workflow code to a vendor."""

import os

from app.config import Settings
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.azure_openai import AzureOpenAIProvider
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider import ModelProvider


def create_provider(settings: Settings) -> ModelProvider:
    provider = settings.model_provider.lower()
    if provider == "mock":
        return MockProvider()
    if provider == "openai":
        return OpenAIProvider(settings.model_name, os.getenv("OPENAI_API_KEY"))
    if provider == "azure_openai":
        return AzureOpenAIProvider(
            deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
    if provider == "anthropic":
        return AnthropicProvider(settings.model_name, os.getenv("ANTHROPIC_API_KEY"))
    raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}")
