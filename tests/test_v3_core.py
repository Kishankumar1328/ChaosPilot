import pytest
from pydantic import BaseModel
from app.models.state import ChaosPilotState, RunStatus
from app.core.llm import (
    LLMFactory, 
    GeminiProvider, 
    OpenAIProvider, 
    AnthropicProvider, 
    OllamaProvider,
    llm_circuit_breaker
)
from app.core.memory.qdrant_store import QdrantVectorMemory
from app.core.observability import record_llm_tokens, record_bug_discovered
from app.agents.graph_v3 import create_chaospilot_v3_graph

class SampleStructuredOutput(BaseModel):
    summary: str
    risk_level: int

@pytest.mark.asyncio
async def test_multimodel_factory_and_providers():
    # Test Factory instantiation
    gemini = LLMFactory.get_provider("gemini")
    openai = LLMFactory.get_provider("openai")
    claude = LLMFactory.get_provider("anthropic")
    ollama = LLMFactory.get_provider("ollama")

    assert isinstance(gemini, GeminiProvider)
    assert isinstance(openai, OpenAIProvider)
    assert isinstance(claude, AnthropicProvider)
    assert isinstance(ollama, OllamaProvider)

    # Test text generation and token usage tracking
    res = await openai.generate_text("Test prompt for OpenAI")
    assert res.provider == "openai"
    assert res.usage.total_tokens > 0
    assert openai.total_prompt_tokens > 0

    # Test structured output Pydantic v2 generation
    structured = await claude.generate_structured(
        prompt="Analyze code risk",
        output_schema=SampleStructuredOutput
    )
    assert isinstance(structured, SampleStructuredOutput)

def test_circuit_breaker():
    assert llm_circuit_breaker.name == "llm_provider_circuit_breaker"
    assert llm_circuit_breaker.fail_max == 5

@pytest.mark.asyncio
async def test_qdrant_vector_memory():
    memory = QdrantVectorMemory(location=":memory:")
    await memory.upsert_dom_snapshot(
        snapshot_id="SNAP-001",
        text_content="Unhandled NullPointerException in SubmitButton.onClick",
        metadata={"route": "/checkout"}
    )

    results = await memory.search_similar_errors("NullPointerException", limit=2)
    assert len(results) > 0
    assert results[0].payload["snapshot_id"] == "SNAP-001"

def test_prometheus_observability():
    record_llm_tokens(provider="gemini", model="gemini-2.5-flash", prompt_tokens=100, completion_tokens=50)
    record_bug_discovered(severity="CRITICAL")

@pytest.mark.asyncio
async def test_v3_10_node_langgraph_workflow():
    graph = create_chaospilot_v3_graph()
    state = ChaosPilotState(
        run_id="V3-TEST-RUN-01",
        target_url="http://127.0.0.1:8888",
        status=RunStatus.DISCOVERING
    )

    final_state = await graph.ainvoke(state)
    assert final_state["status"] == RunStatus.COMPLETED
    assert len(final_state["logs"]) >= 10
    assert any("[10. REPORTING]" in log for log in final_state["logs"])
