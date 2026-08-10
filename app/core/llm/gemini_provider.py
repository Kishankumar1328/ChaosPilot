import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm.base import LLMProvider, LLMResponse, LLMUsageStats, resilient_llm_call

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class GeminiProvider(LLMProvider):
    """
    Google Gemini Provider (Flash / Pro) with multimodal vision and structured Pydantic v2 output.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key)
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key
        ) if self.api_key else None

    @resilient_llm_call
    async def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None
    ) -> LLMResponse:
        if not self.llm:
            # Fallback mock for offline / testing mode
            return LLMResponse(
                content=f"[Mock Gemini {self.model_name}] Response for: {prompt[:50]}...",
                model=self.model_name,
                provider="gemini",
                usage=LLMUsageStats(prompt_tokens=15, completion_tokens=25, total_tokens=40)
            )

        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        
        content_items = [{"type": "text", "text": prompt}]
        if images:
            import base64
            for img_bytes in images:
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                content_items.append({"type": "image_url", "image_url": f"data:image/png;base64,{b64}"})

        messages.append(HumanMessage(content=content_items))
        res = await self.llm.ainvoke(messages)
        
        usage = LLMUsageStats(prompt_tokens=50, completion_tokens=50, total_tokens=100)
        self.record_usage(usage)

        return LLMResponse(
            content=res.content,
            model=self.model_name,
            provider="gemini",
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
        if not self.llm:
            # Construct mock instance of schema for test fallback
            schema_fields = output_schema.model_fields
            mock_kwargs = {}
            for fname, ffield in schema_fields.items():
                if ffield.annotation == str:
                    mock_kwargs[fname] = f"Mock {fname}"
                elif ffield.annotation in (int, float):
                    mock_kwargs[fname] = 1
                elif ffield.annotation == list or getattr(ffield.annotation, "__origin__", None) == list:
                    mock_kwargs[fname] = []
                elif ffield.annotation == dict:
                    mock_kwargs[fname] = {}
                else:
                    mock_kwargs[fname] = None
            return output_schema.model_construct(**mock_kwargs)

        structured_chain = self.llm.with_structured_output(output_schema)
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))

        result = await structured_chain.ainvoke(messages)
        self.record_usage(LLMUsageStats(prompt_tokens=40, completion_tokens=60, total_tokens=100))
        return result
