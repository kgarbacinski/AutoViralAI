"""Tests for learning pipeline graph compilation."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from config.settings import Settings
from src.graphs.learning_pipeline import build_learning_pipeline


def test_learning_pipeline_compiles():
    """Verify the learning pipeline graph compiles without errors."""
    settings = Settings(
        anthropic_api_key="test-key",
        account_id="test",
        env="development",
    )
    store = InMemoryStore()
    graph = build_learning_pipeline(settings, store)
    compiled = graph.compile(checkpointer=MemorySaver())
    assert compiled is not None


def test_learning_pipeline_has_correct_nodes():
    """Verify all expected nodes are present."""
    settings = Settings(
        anthropic_api_key="test-key",
        account_id="test",
        env="development",
    )
    store = InMemoryStore()
    graph = build_learning_pipeline(settings, store)

    expected_nodes = {
        "collect_metrics",
        "analyze_performance",
        "update_knowledge_base",
        "adjust_strategy",
    }

    actual_nodes = set(graph.nodes.keys())
    assert expected_nodes.issubset(actual_nodes), f"Missing nodes: {expected_nodes - actual_nodes}"
