"""Shared dependency getters/setters for bot handlers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.orchestrator import PipelineOrchestrator
    from src.store.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

_knowledge_base: KnowledgeBase | None = None
_orchestrator: PipelineOrchestrator | None = None
_authorized_chat_id: int | None = None


def set_knowledge_base(kb: KnowledgeBase) -> None:
    global _knowledge_base
    _knowledge_base = kb


def get_knowledge_base() -> KnowledgeBase | None:
    return _knowledge_base


def set_orchestrator(orchestrator: PipelineOrchestrator) -> None:
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator() -> PipelineOrchestrator | None:
    return _orchestrator


def set_authorized_chat_id(chat_id: str) -> None:
    global _authorized_chat_id
    _authorized_chat_id = int(chat_id) if chat_id else None


def get_authorized_chat_id() -> int | None:
    return _authorized_chat_id
