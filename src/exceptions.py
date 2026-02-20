class AutoViralError(Exception):
    """Base for all AutoViralAI domain errors."""


class KnowledgeBaseError(AutoViralError):
    """Store read/write failed (wraps psycopg, Pydantic validation, etc.)."""


class PipelineError(AutoViralError):
    """LangGraph pipeline execution failed at graph level."""
