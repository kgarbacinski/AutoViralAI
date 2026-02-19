from functools import partial

from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph

from config.settings import Settings
from src.models.state import LearningPipelineState
from src.nodes.analysis import analyze_performance
from src.nodes.learning import update_knowledge_base
from src.nodes.metrics import collect_metrics
from src.nodes.strategy import adjust_strategy
from src.store.knowledge_base import KnowledgeBase
from src.tools.threads_api import ThreadsClient, get_threads_client


def build_learning_pipeline(
    settings: Settings,
    store,
    threads_client: ThreadsClient | None = None,
) -> StateGraph:
    llm = ChatAnthropic(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
        max_retries=3,
    )
    threads_client = threads_client or get_threads_client(settings)
    kb = KnowledgeBase(store=store, account_id=settings.account_id)

    graph = StateGraph(LearningPipelineState)

    graph.add_node(
        "collect_metrics",
        partial(collect_metrics, threads_client=threads_client, kb=kb),
    )
    graph.add_node(
        "analyze_performance",
        partial(analyze_performance, llm=llm, kb=kb),
    )
    graph.add_node(
        "update_knowledge_base",
        partial(update_knowledge_base, kb=kb),
    )
    graph.add_node(
        "adjust_strategy",
        partial(adjust_strategy, llm=llm, kb=kb),
    )

    graph.add_edge(START, "collect_metrics")
    graph.add_conditional_edges(
        "collect_metrics",
        lambda state: "continue" if state.get("collected_metrics") else "end",
        {"continue": "analyze_performance", "end": END},
    )
    graph.add_edge("analyze_performance", "update_knowledge_base")
    graph.add_edge("update_knowledge_base", "adjust_strategy")
    graph.add_edge("adjust_strategy", END)

    return graph
