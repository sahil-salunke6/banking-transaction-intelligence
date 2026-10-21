import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_python_with_env(code: str, overrides: dict[str, str]) -> str:
    """Run Python in a separate process with controlled environment settings."""
    env = os.environ.copy()

    env.pop("APP_ENV", None)
    env.pop("API_DOCS_ENABLED", None)
    env.pop("API_KEY_REQUIRED", None)

    env.update(overrides)

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def test_production_requires_api_key_even_when_disabled_requested():
    output = run_python_with_env(
        "from app.config import API_KEY_REQUIRED; print(API_KEY_REQUIRED)",
        {
            "APP_ENV": "production",
            "API_KEY_REQUIRED": "false",
        },
    )

    assert output == "True"


def test_production_disables_api_docs_by_default():
    code = (
        "from app.main import app; "
        "assert app.docs_url is None; "
        "assert app.redoc_url is None; "
        "assert app.openapi_url is None; "
        "print('Production documentation disabled')"
    )

    output = run_python_with_env(
        code,
        {
            "APP_ENV": "production",
            "API_KEY_REQUIRED": "false",
        },
    )

    assert output == "Production documentation disabled"
