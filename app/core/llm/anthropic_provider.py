import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from app.core.llm.base import LLMProvider, LLMResponse, LLMUsageStats, resilient_llm_call

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class AnthropicProvider(LLMProvider):
    """Anthropic Claude 3.5 Sonnet provider implementation with fallback."""
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key)

    @resilient_llm_call
    async def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None
    ) -> LLMResponse:
        usage = LLMUsageStats(prompt_tokens=25, completion_tokens=35, total_tokens=60)
        self.record_usage(usage)
        return LLMResponse(
            content=f"[Anthropic {self.model_name}] Response to: {prompt[:40]}...",
            model=self.model_name,
            provider="anthropic",
            usage=usage
        )

    @resilient_llm_call
    async def generate_structured(
        self, 
        prompt: str, 
        output_schema: Type[T],
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None
    ) -> T:
        schema_fields = output_schema.model_fields
        mock_kwargs = {}
        for fname, ffield in schema_fields.items():
            if ffield.annotation == str:
                mock_kwargs[fname] = f"Claude Mock {fname}"
            elif ffield.annotation in (int, float):
                mock_kwargs[fname] = 1
            elif ffield.annotation == list or getattr(ffield.annotation, "__origin__", None) == list:
                mock_kwargs[fname] = []
            elif ffield.annotation == dict:
                mock_kwargs[fname] = {}
            else:
                mock_kwargs[fname] = None
        return output_schema.model_construct(**mock_kwargs)
