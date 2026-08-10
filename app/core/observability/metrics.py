import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Prometheus Observability Metrics for ChaosPilot v3.0
TEST_EXECUTION_TIME = Histogram(
    "chaospilot_test_execution_seconds",
    "Time spent executing automated test suites in seconds",
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

LLM_TOKEN_USAGE = Counter(
    "chaospilot_llm_token_usage_total",
    "Total LLM tokens consumed across multi-model providers",
    ["provider", "model", "token_type"]
)

CRAWLER_COVERAGE_PERCENT = Gauge(
    "chaospilot_crawler_coverage_percent",
    "Percentage of target web application routes mapped"
)

SELF_HEAL_SUCCESS_RATE = Counter(
    "chaospilot_self_heal_success_total",
    "Total number of successful self-healing step interventions"
)

BUG_DISCOVERY_COUNT = Counter(
    "chaospilot_bugs_discovered_total",
    "Total vulnerabilities and uncaught exceptions discovered",
    ["severity"]
)

def record_llm_tokens(provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    LLM_TOKEN_USAGE.labels(provider=provider, model=model, token_type="prompt").inc(prompt_tokens)
    LLM_TOKEN_USAGE.labels(provider=provider, model=model, token_type="completion").inc(completion_tokens)

def record_bug_discovered(severity: str):
    BUG_DISCOVERY_COUNT.labels(severity=severity).inc()
