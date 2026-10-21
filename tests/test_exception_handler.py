
import asyncio
import json
import logging

from starlette.requests import Request

from app.main import app


def test_unexpected_exception_returns_safe_500_response(
    caplog,
):
    handler = app.exception_handlers[Exception]

    request = Request({
        "type": "http",
        "asgi": {
            "version": "3.0",
            "spec_version": "2.3",
        },
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/test-error",
        "raw_path": b"/test-error",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
    })

    error = RuntimeError("Internal test detail")

    with caplog.at_level(logging.ERROR):
        response = asyncio.run(handler(request, error))

    response_body = json.loads(response.body)

    assert response.status_code == 500
    assert response_body == {
        "detail": "An unexpected internal server error occurred."
    }

    assert "Unhandled application exception" in caplog.text
    assert "Internal test detail" in caplog.text
