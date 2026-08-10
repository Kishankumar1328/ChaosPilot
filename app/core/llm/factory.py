import logging
from typing import Dict, Optional
from app.config import settings
from app.core.llm.base import LLMProvider
from app.core.llm.gemini_provider import GeminiProvider
from app.core.llm.openai_provider import OpenAIProvider
from app.core.llm.anthropic_provider import AnthropicProvider
from app.core.llm.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class LLMFactory:
    """
    Factory Pattern for Multi-Model AI Orchestration in ChaosPilot v3.0.
    Manages provider selection, model instances, and token usage metrics across services.
    """
    _providers: Dict[str, LLMProvider] = {}

    @classmethod
    def get_provider(
        cls, 
        provider_name: str = "gemini", 
        model_name: Optional[str] = None
    ) -> LLMProvider:
        key = f"{provider_name}:{model_name or 'default'}"
        if key in cls._providers:
            return cls._providers[key]

        provider_name = provider_name.lower()
        if provider_name == "gemini":
            provider = GeminiProvider(
                model_name=model_name or settings.GEMINI_MODEL_FAST,
                api_key=settings.GEMINI_API_KEY
            )
        elif provider_name == "openai":
            provider = OpenAIProvider(
                model_name=model_name or "gpt-4o"
            )
        elif provider_name == "anthropic":
            provider = AnthropicProvider(
                model_name=model_name or "claude-3-5-sonnet-20241022"
            )
        elif provider_name == "ollama":
            provider = OllamaProvider(
                model_name=model_name or "llama3:latest"
            )
        else:
            logger.warning(f"Unknown LLM provider '{provider_name}'. Defaulting to Gemini.")
            provider = GeminiProvider(
                model_name=settings.GEMINI_MODEL_FAST,
                api_key=settings.GEMINI_API_KEY
            )

        cls._providers[key] = provider
        logger.info(f"Initialized LLMProvider: {provider_name} ({provider.model_name})")
        return provider
