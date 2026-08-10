import abc
import logging
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    """Raised when the circuit breaker is in OPEN state."""
    pass

class AsyncCircuitBreaker:
    """
    Native Async Circuit Breaker for LLM Multi-Model Provider Orchestration.
    Opens after `fail_max` consecutive failures and auto-resets after `reset_timeout` seconds.
    """
    def __init__(self, fail_max: int = 5, reset_timeout: float = 30.0, name: str = "llm_circuit_breaker"):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    async def call(self, func, *args, **kwargs):
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_failure_time > self.reset_timeout:
                self.state = "HALF-OPEN"
                logger.info(f"CircuitBreaker '{self.name}' transitioning to HALF-OPEN.")
            else:
                raise CircuitBreakerOpenException(f"CircuitBreaker '{self.name}' is OPEN. Requests blocked.")

        try:
            res = await func(*args, **kwargs)
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info(f"CircuitBreaker '{self.name}' reset to CLOSED.")
            return res
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = now
            if self.failure_count >= self.fail_max:
                self.state = "OPEN"
                logger.warning(f"CircuitBreaker '{self.name}' tripped OPEN after {self.failure_count} failures: {e}")
            raise e

llm_circuit_breaker = AsyncCircuitBreaker(fail_max=5, reset_timeout=30.0, name="llm_provider_circuit_breaker")

T = TypeVar("T", bound=BaseModel)

class LLMUsageStats(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class LLMResponse(BaseModel):
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    usage: LLMUsageStats = Field(default_factory=LLMUsageStats)
    model: str
    provider: str

class LLMProvider(abc.ABC):
    """
    Abstract Base Class for Multi-Model AI Orchestration in ChaosPilot v3.0.
    Supports structured JSON output, vision multimodal inputs, token tracking, and circuit breakers.
    """
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    @abc.abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None
    ) -> LLMResponse:
        """Generate raw text or vision-grounded response."""
        pass

    @abc.abstractmethod
    async def generate_structured(
        self, 
        prompt: str, 
        output_schema: Type[T],
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None
    ) -> T:
        """Generate strictly validated Pydantic v2 structured output."""
        pass

    def record_usage(self, usage: LLMUsageStats):
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        logger.debug(
            f"[{self.__class__.__name__}] Usage logged: +{usage.total_tokens} tokens (Total: {self.total_prompt_tokens + self.total_completion_tokens})"
        )

def resilient_llm_call(func):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def wrapper(*args, **kwargs):
        return await llm_circuit_breaker.call(func, *args, **kwargs)
    return wrapper
