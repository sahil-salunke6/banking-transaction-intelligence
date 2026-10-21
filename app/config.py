
import os


def get_bool_env(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

if APP_ENV not in {"development", "production", "test"}:
    raise ValueError(
        "APP_ENV must be development, production, or test."
    )

API_DOCS_ENABLED = get_bool_env(
    "API_DOCS_ENABLED",
    default=(APP_ENV != "production"),
)

API_KEY_REQUIRED = APP_ENV == "production" or get_bool_env(
    "API_KEY_REQUIRED",
    default=True,
)
