from functools import partial

from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph

from config.settings import Settings
from src.models.state import CreationPipelineState
from src.nodes.approval import human_approval
from src.nodes.generation import generate_post_variants
from src.nodes.goal_check import goal_check
from src.nodes.patterns import extract_patterns
from src.nodes.publishing import publish_post, schedule_metrics_check
from src.nodes.ranking import rank_and_select
from src.nodes.research import research_viral_content
from src.store.knowledge_base import KnowledgeBase
from src.tools.apify_client import ThreadsScraper, get_threads_scraper
from src.tools.embeddings import EmbeddingClient
from src.tools.hackernews_client import HackerNewsClient, get_hackernews_client
from src.tools.threads_api import ThreadsClient, get_threads_client


def build_creation_pipeline(
    settings: Settings,
    store,
    threads_client: ThreadsClient | None = None,
    hn: HackerNewsClient | None = None,
    scraper: ThreadsScraper | None = None,
    embedding_client: EmbeddingClient | None = None,
) -> StateGraph:
    llm = ChatAnthropic(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
        max_retries=8,
    )
    threads_client = threads_client or get_threads_client(settings)
    hn = hn or get_hackernews_client(settings)
    scraper = scraper or get_threads_scraper(settings)
    embedding_client = embedding_client or EmbeddingClient()
    kb = KnowledgeBase(store=store, account_id=settings.account_id)

    graph = StateGraph(CreationPipelineState)

    graph.add_node(
        "goal_check",
        partial(goal_check, threads_client=threads_client),
    )
    graph.add_node(
        "research_viral_content",
        partial(research_viral_content, hn=hn, scraper=scraper, kb=kb),
    )
    graph.add_node(
        "extract_patterns",
        partial(extract_patterns, llm=llm, kb=kb),
    )
    graph.add_node(
        "generate_post_variants",
        partial(generate_post_variants, llm=llm, kb=kb),
    )
    graph.add_node(
        "rank_and_select",
        partial(rank_and_select, llm=llm, kb=kb, embedding_client=embedding_client),
    )
    graph.add_node(
        "human_approval",
        human_approval,
    )
    graph.add_node(
        "publish_post",
        partial(publish_post, threads_client=threads_client, kb=kb),
    )
    graph.add_node(
        "schedule_metrics_check",
        partial(schedule_metrics_check, kb=kb),
    )

    graph.add_edge(START, "goal_check")

    graph.add_conditional_edges(
        "goal_check",
        _should_continue,
        {"end": END, "continue": "research_viral_content"},
    )

    graph.add_edge("research_viral_content", "extract_patterns")
    graph.add_edge("extract_patterns", "generate_post_variants")
    graph.add_edge("generate_post_variants", "rank_and_select")
    graph.add_edge("rank_and_select", "human_approval")

    graph.add_conditional_edges(
        "human_approval",
        _after_approval,
        {
            "publish": "publish_post",
            "regenerate": "generate_post_variants",
            "end": END,
        },
    )

    graph.add_edge("publish_post", "schedule_metrics_check")
    graph.add_edge("schedule_metrics_check", END)

    return graph


def _should_continue(state: CreationPipelineState) -> str:
    if state.get("goal_reached"):
        return "end"
    return "continue"


def _after_approval(state: CreationPipelineState) -> str:
    decision = state.get("human_decision", "reject")
    if decision in ("approve", "edit"):
        return "publish"
    feedback = state.get("human_feedback", "")
    if decision == "reject" and feedback:
        return "regenerate"
    return "end"
