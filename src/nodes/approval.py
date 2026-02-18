"""Human approval node - uses LangGraph interrupt() for human-in-the-loop."""

from langgraph.types import interrupt

from src.models.state import CreationPipelineState


async def human_approval(state: CreationPipelineState) -> dict:
    """Present the top-ranked post for human approval via interrupt.

    The interrupt mechanism pauses the graph and waits for human input.
    In production, a Telegram bot picks up the interrupt and presents
    the post to the user with Approve/Edit/Reject buttons.
    """
    selected = state.get("selected_post")
    ranked = state.get("ranked_posts", [])

    if not selected:
        return {
            "human_decision": "reject",
            "errors": ["human_approval: No post selected for approval"],
        }

    alternatives = ranked[1:3] if len(ranked) > 1 else []
    approval_payload = {
        "selected_post": selected,
        "alternatives": alternatives,
        "cycle_number": state.get("cycle_number", 0),
        "follower_count": state.get("current_follower_count", 0),
    }

    decision = interrupt(approval_payload)

    human_decision = decision.get("decision", "reject")
    human_edited = decision.get("edited_content")
    human_feedback = decision.get("feedback")

    if human_decision == "edit" and human_edited:
        selected = {**selected, "content": human_edited}

    return {
        "selected_post": selected if human_decision != "reject" else state.get("selected_post"),
        "human_decision": human_decision,
        "human_edited_content": human_edited,
        "human_feedback": human_feedback,
    }
