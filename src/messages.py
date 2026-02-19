# --- Persistence ---
MEMORY_CHECKPOINTER_NOT_FOR_PROD = (
    "In-memory checkpointer is not suitable for production. "
    "Use create_postgres_checkpointer() as an async context manager."
)
MEMORY_STORE_NOT_FOR_PROD = (
    "In-memory store is not suitable for production. "
    "Use create_postgres_store() as an async context manager."
)

# --- Threads API ---
THREADS_CONTAINER_FAILED = "Threads container {container_id} failed: {error_msg}"
THREADS_CONTAINER_TIMEOUT = (
    "Threads container {container_id} did not finish after {max_attempts} attempts"
)
THREADS_ACCESS_TOKEN_REQUIRED = (
    "THREADS_ACCESS_TOKEN is required in production. "
    "Get it from https://developers.facebook.com (Threads API)."
)
THREADS_USER_ID_REQUIRED = "THREADS_USER_ID is required in production."

# --- Apify ---
APIFY_TOKEN_REQUIRED = (
    "APIFY_API_TOKEN is required in production. "
    "Get it from https://console.apify.com/account/integrations"
)

# --- Reddit ---
REDDIT_CREDENTIALS_REQUIRED = (
    "{missing} required in production. Get credentials from https://www.reddit.com/prefs/apps"
)

# --- Publishing ---
PUBLISH_NO_POST = "publish_post: No post to publish"
PUBLISH_EMPTY_CONTENT = "publish_post: Post content is empty"
PUBLISH_CONTENT_TOO_LONG = "publish_post: Content exceeds {max_length} chars ({actual_length})"
PUBLISH_FAILED = "publish_post: Failed to publish: {error}"
SCHEDULE_NO_PUBLISHED_POST = "schedule_metrics_check: No published post to schedule"

# --- Approval node ---
APPROVAL_NO_POST = "human_approval: No post selected for approval"
APPROVAL_INVALID_DECISION = "human_approval: Invalid decision type: {type_name}"
