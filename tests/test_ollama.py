"""
Unit tests for Ollama Service Module.
Tests error handling when Ollama is offline or model is missing.
"""

from backend.ollama_service import check_ollama_status, generate_local_completion


def test_ollama_status_offline():
    """Verifies graceful handling when Ollama port is not running."""
    # Use invalid local port
    status = check_ollama_status(base_url="http://localhost:59999", timeout=1.0)
    assert status["connected"] is False
    assert status["models"] == []
    assert status["has_target_model"] is False
    assert status["error_message"] is not None
    assert "Cannot connect" in status["error_message"] or "failed" in status["error_message"].lower()


def test_generate_completion_offline():
    """Verifies completion returns clear error rather than raising uncaught exception."""
    ok, text, err = generate_local_completion(
        prompt="Test",
        base_url="http://localhost:59999",
        timeout=1,
    )
    assert ok is False
    assert text is None
    assert err is not None
    assert "not reachable" in err or "connect" in err.lower()
