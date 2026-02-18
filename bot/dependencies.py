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
