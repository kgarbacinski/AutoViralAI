"""LangGraph Store namespace constants."""


def ns_config(account_id: str) -> tuple[str, str]:
    return ("config", account_id)


def ns_strategy(account_id: str) -> tuple[str, str]:
    return ("strategy", account_id)


def ns_patterns(account_id: str) -> tuple[str, str]:
    return ("patterns", account_id)


def ns_pattern_performance(account_id: str) -> tuple[str, str]:
    return ("pattern_performance", account_id)


def ns_published_posts(account_id: str) -> tuple[str, str]:
    return ("published_posts", account_id)


def ns_pending_metrics(account_id: str) -> tuple[str, str]:
    return ("pending_metrics", account_id)


def ns_metrics_history(account_id: str) -> tuple[str, str]:
    return ("metrics_history", account_id)


def ns_research_cache(account_id: str) -> tuple[str, str]:
    return ("research_cache", account_id)
