
import hmac
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import API_KEY_REQUIRED


API_KEY_ENV_VAR = "BANKING_API_KEY"

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def require_api_key(
    api_key: str | None = Security(api_key_header),
) -> None:
    """Enforce API-key authentication according to application config."""

    # Development can explicitly disable authentication.
    # Production cannot, because app.config forces this setting to True.
    if not API_KEY_REQUIRED:
        return

    expected_api_key = os.getenv(API_KEY_ENV_VAR)

    if not expected_api_key or not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    if not hmac.compare_digest(api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
