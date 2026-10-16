
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api import app


@pytest.fixture
def client():
    # Supply a mock pipeline so API tests don't need a real
    # embedding model, PDF index, or Groq API call.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        app.state.pipeline = MagicMock()
        yield test_client
        app.state.pipeline = None


def test_health_reports_ready(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "index_ready": True,
    }


def test_ask_returns_pipeline_result(client):
    app.state.pipeline.answer.return_value = {
        "question": "What does top management do?",
        "answer": "Top management demonstrates leadership.",
        "status": "supported",
        "claims": [],
        "evidence": [],
        "abstained": False,
        "abstention_reason": None,
        "limitations": [],
    }

    response = client.post(
        "/ask",
        json={
            "question": "What does top management do?",
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "supported"
    app.state.pipeline.answer.assert_called_once_with(
        question="What does top management do?",
        top_k=5,
    )


def test_ask_returns_503_when_index_not_ready(client):
    app.state.pipeline = None

    response = client.post(
        "/ask",
        json={"question": "What does top management do?"},
    )

    assert response.status_code == 503


def test_ask_rejects_empty_question(client):
    response = client.post(
        "/ask",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_ask_rejects_invalid_top_k(client):
    response = client.post(
        "/ask",
        json={
            "question": "What does top management do?",
            "top_k": 0,
        },
    )

    assert response.status_code == 422


def test_ask_hides_internal_pipeline_errors(client):
    app.state.pipeline.answer.side_effect = RuntimeError(
        "Internal provider details"
    )

    response = client.post(
        "/ask",
        json={"question": "What does top management do?"},
    )

    assert response.status_code == 502
    assert "Internal provider details" not in response.text
