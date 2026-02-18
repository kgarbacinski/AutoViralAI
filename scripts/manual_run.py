"""Manual single-cycle run for testing.

Usage:
    uv run python scripts/manual_run.py [--pipeline creation|learning] [--auto-approve]
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import yaml
from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings
from src.graphs.creation_pipeline import build_creation_pipeline
from src.graphs.learning_pipeline import build_learning_pipeline
from src.models.strategy import AccountNiche, AudienceConfig, ContentPillar, VoiceConfig
from src.persistence import create_checkpointer, create_store
from src.store.knowledge_base import KnowledgeBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def init_niche_config(kb: KnowledgeBase) -> None:
    """Initialize niche config in the store if not present."""
    existing = await kb.get_niche_config()
    if existing:
        return

    settings = get_settings()
    config_path = settings.niche_config_path
    if config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f)
    else:
        raw = {}

    niche = AccountNiche(
        niche=raw.get("niche", "tech"),
        sub_niche=raw.get("sub_niche", "programming & startups"),
        description=raw.get("description", ""),
        voice=VoiceConfig(
            tone=raw.get("voice", {}).get("tone", "conversational"),
            persona=raw.get("voice", {}).get("persona", "tech expert"),
            style_notes=raw.get("voice", {}).get("style_notes", []),
        ),
        audience=AudienceConfig(
            primary=raw.get("audience", {}).get("primary", "developers"),
            secondary=raw.get("audience", {}).get("secondary", "tech enthusiasts"),
            pain_points=raw.get("audience", {}).get("pain_points", []),
        ),
        content_pillars=[
            ContentPillar(name=p["name"], description=p["description"], weight=p["weight"])
            for p in raw.get("content_pillars", [])
        ],
        avoid_topics=raw.get("avoid_topics", []),
        hashtags_primary=raw.get("hashtags", {}).get("primary", []),
        hashtags_secondary=raw.get("hashtags", {}).get("secondary", []),
        max_hashtags_per_post=raw.get("hashtags", {}).get("max_per_post", 3),
        posting_timezone=raw.get("posting_schedule", {}).get("timezone", "Europe/Warsaw"),
        preferred_posting_times=raw.get("posting_schedule", {}).get("preferred_times", []),
        max_posts_per_day=raw.get("posting_schedule", {}).get("max_posts_per_day", 3),
    )

    await kb.save_niche_config(niche)
    logger.info("Niche config initialized in store")


async def run_creation_pipeline(auto_approve: bool = False) -> None:
    """Run a single creation pipeline cycle."""
    settings = get_settings()
    store = create_store(settings)
    checkpointer = create_checkpointer(settings)

    kb = KnowledgeBase(store=store, account_id=settings.account_id)
    await init_niche_config(kb)

    graph = build_creation_pipeline(settings, store)
    compiled = graph.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "manual_creation_1"}}

    initial_state = {
        "current_follower_count": 0,
        "target_follower_count": settings.target_followers,
        "goal_reached": False,
        "viral_posts": [],
        "extracted_patterns": [],
        "generated_variants": [],
        "ranked_posts": [],
        "selected_post": None,
        "human_decision": None,
        "human_edited_content": None,
        "human_feedback": None,
        "published_post": None,
        "cycle_number": 1,
        "errors": [],
    }

    logger.info("Starting creation pipeline...")

    async for event in compiled.astream(initial_state, config):
        for node_name, node_output in event.items():
            logger.info(f"Node [{node_name}] completed")
            if node_name == "rank_and_select" and node_output.get("selected_post"):
                post = node_output["selected_post"]
                logger.info(f"  Selected post (score: {post.get('composite_score', 0):.1f}):")
                logger.info(f"  {post.get('content', '')[:200]}")

    state = await compiled.aget_state(config)
    if state.next and "human_approval" in state.next:
        logger.info("\n--- HUMAN APPROVAL REQUIRED ---")

        if auto_approve:
            logger.info("Auto-approving...")
            decision = {"decision": "approve"}
        else:
            # Interactive approval
            selected = state.values.get("selected_post", {})
            print(f"\nPost for approval:\n{selected.get('content', 'N/A')}")
            print(f"Pattern: {selected.get('pattern_used', 'N/A')}")
            print(f"Score: {selected.get('composite_score', 0):.1f}/10")
            print()

            ranked = state.values.get("ranked_posts", [])
            if len(ranked) > 1:
                print("Alternatives:")
                for alt in ranked[1:3]:
                    print(
                        f"  [{alt.get('composite_score', 0):.1f}] {alt.get('content', '')[:100]}..."
                    )
                print()

            choice = input("(a)pprove / (r)eject / (e)dit: ").strip().lower()
            if choice == "a":
                decision = {"decision": "approve"}
            elif choice == "e":
                edited = input("Enter edited content: ").strip()
                decision = {"decision": "edit", "edited_content": edited}
            else:
                feedback = input("Rejection reason (optional): ").strip()
                decision = {"decision": "reject", "feedback": feedback}

        async for event in compiled.astream(Command(resume=decision), config):
            for node_name, node_output in event.items():
                logger.info(f"Node [{node_name}] completed")
                if node_name == "publish_post" and node_output.get("published_post"):
                    post = node_output["published_post"]
                    logger.info(f"  Published! ID: {post.get('threads_id', 'N/A')}")

    final_state = await compiled.aget_state(config)
    errors = final_state.values.get("errors", [])
    if errors:
        logger.warning(f"Errors: {errors}")
    logger.info("Creation pipeline complete!")


async def run_learning_pipeline() -> None:
    """Run a single learning pipeline cycle."""
    settings = get_settings()
    store = create_store(settings)
    checkpointer = create_checkpointer(settings)

    graph = build_learning_pipeline(settings, store)
    compiled = graph.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "manual_learning_1"}}

    initial_state = {
        "posts_to_check": [],
        "collected_metrics": [],
        "performance_analysis": None,
        "pattern_updates": [],
        "new_strategy": None,
        "cycle_number": 1,
        "errors": [],
    }

    logger.info("Starting learning pipeline...")

    async for event in compiled.astream(initial_state, config):
        for node_name, node_output in event.items():
            logger.info(f"Node [{node_name}] completed")

    final_state = await compiled.aget_state(config)
    errors = final_state.values.get("errors", [])
    if errors:
        logger.warning(f"Errors: {errors}")

    new_strategy = final_state.values.get("new_strategy")
    if new_strategy:
        logger.info(f"Updated strategy (iteration {new_strategy.get('iteration', 0)}):")
        for learning in new_strategy.get("key_learnings", []):
            logger.info(f"  - {learning}")

    logger.info("Learning pipeline complete!")


def main():
    parser = argparse.ArgumentParser(description="Manual pipeline run")
    parser.add_argument(
        "--pipeline",
        choices=["creation", "learning"],
        default="creation",
        help="Which pipeline to run",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve posts (skip human approval)",
    )
    args = parser.parse_args()

    if args.pipeline == "creation":
        asyncio.run(run_creation_pipeline(auto_approve=args.auto_approve))
    else:
        asyncio.run(run_learning_pipeline())


if __name__ == "__main__":
    main()
