import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from app.core.llm.base import LLMProvider, LLMResponse, LLMUsageStats, resilient_llm_call

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class OllamaProvider(LLMProvider):
    """Ollama Local LLM Provider (Llama3 / Qwen / DeepSeek-R1)."""
    def __init__(self, model_name: str = "llama3:latest", host: str = "http://localhost:11434"):
        super().__init__(model_name=model_name, api_key=None)
        self.host = host

    @resilient_llm_call
    async def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None
    ) -> LLMResponse:
        usage = LLMUsageStats(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        self.record_usage(usage)
        return LLMResponse(
            content=f"[Ollama {self.model_name}] Local Response: {prompt[:40]}...",
            model=self.model_name,
            provider="ollama",
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
                mock_kwargs[fname] = f"Ollama Mock {fname}"
            elif ffield.annotation in (int, float):
                mock_kwargs[fname] = 1
            elif ffield.annotation == list or getattr(ffield.annotation, "__origin__", None) == list:
                mock_kwargs[fname] = []
            elif ffield.annotation == dict:
                mock_kwargs[fname] = {}
            else:
                mock_kwargs[fname] = None
        return output_schema.model_construct(**mock_kwargs)
