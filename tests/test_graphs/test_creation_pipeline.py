"""Tests for creation pipeline graph compilation."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from config.settings import Settings
from src.graphs.creation_pipeline import build_creation_pipeline


def test_creation_pipeline_compiles():
    """Verify the creation pipeline graph compiles without errors."""
    settings = Settings(
        anthropic_api_key="test-key",
        account_id="test",
        env="development",
    )
    store = InMemoryStore()
    graph = build_creation_pipeline(settings, store)
    compiled = graph.compile(checkpointer=MemorySaver())
    assert compiled is not None


def test_creation_pipeline_has_correct_nodes():
    """Verify all expected nodes are present."""
    settings = Settings(
        anthropic_api_key="test-key",
        account_id="test",
        env="development",
    )
    store = InMemoryStore()
    graph = build_creation_pipeline(settings, store)

    expected_nodes = {
        "goal_check",
        "research_viral_content",
        "extract_patterns",
        "generate_post_variants",
        "rank_and_select",
        "human_approval",
        "publish_post",
        "schedule_metrics_check",
    }

    actual_nodes = set(graph.nodes.keys())
    assert expected_nodes.issubset(actual_nodes), f"Missing nodes: {expected_nodes - actual_nodes}"
