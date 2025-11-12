"""
Unit Tests for Ollama Chat Application API

This module contains comprehensive unit tests for all API endpoints
and core functionality. Tests cover:
- Happy paths (successful operations)
- Error cases (validation, connectivity)
- Edge cases (empty messages, timeouts, etc.)
- Type correctness

Test Coverage:
- Health check endpoint
- Models listing endpoint
- Chat endpoint (streaming and buffered)
- Application info endpoint
- UI serving endpoint
- Error handling
- Input validation

Usage:
    pytest tests/test_chat_api.py -v
    pytest tests/test_chat_api.py --cov=src

Author: Keren
Version: 1.0.0
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from fastapi import HTTPException
import requests
from requests.exceptions import ConnectionError, Timeout

# Import the application
from main import app, validate_message, Config

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture
def mock_ollama_healthy():
    """Mock successful Ollama health check response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "models": [
            {"name": "tinyllama"},
            {"name": "llama2"}
        ]
    }
    return response

@pytest.fixture
def mock_ollama_unhealthy():
    """Mock failed Ollama health check response."""
    response = Mock()
    response.status_code = 503
    return response

# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidateMessage:
    """Tests for message validation function."""

    def test_valid_message(self):
        """Test validation of a normal message."""
        result = validate_message("Hello, world!")
        assert result == "Hello, world!"

    def test_message_with_whitespace(self):
        """Test that whitespace is stripped."""
        result = validate_message("  Hello, world!  ")
        assert result == "Hello, world!"

    def test_empty_message_raises_error(self):
        """Test that empty message raises ValueError."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            validate_message("")

    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only message raises ValueError."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            validate_message("   ")

    def test_message_too_long_raises_error(self):
        """Test that message exceeding 4000 chars raises ValueError."""
        long_message = "x" * 4001
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_message(long_message)

    def test_message_at_max_length(self):
        """Test that message at exactly 4000 chars is accepted."""
        message = "x" * 4000
        result = validate_message(message)
        assert len(result) == 4000

    def test_multiline_message(self):
        """Test that multiline messages are handled."""
        message = "Line 1\nLine 2\nLine 3"
        result = validate_message(message)
        assert result == "Line 1\nLine 2\nLine 3"

# ============================================================================
# HEALTH CHECK ENDPOINT TESTS
# ============================================================================

class TestHealthCheckEndpoint:
    """Tests for GET /api/health endpoint."""

    @patch('main.requests.get')
    def test_health_check_success(self, mock_get, client, mock_ollama_healthy):
        """Test successful health check when Ollama is running."""
        mock_get.return_value = mock_ollama_healthy

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["ollama"] == "connected"
        assert data["model"] == Config.MODEL_NAME

    @patch('main.requests.get')
    def test_health_check_ollama_down(self, mock_get, client):
        """Test health check when Ollama is not running."""
        mock_get.side_effect = ConnectionError("Connection refused")

        response = client.get("/api/health")

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Ollama" in data["detail"] or "not available" in data["detail"]

    @patch('main.requests.get')
    def test_health_check_timeout(self, mock_get, client):
        """Test health check with timeout."""
        mock_get.side_effect = Timeout("Request timeout")

        response = client.get("/api/health")

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data

    @patch('main.requests.get')
    def test_health_check_non_200_response(self, mock_get, client):
        """Test health check when Ollama returns non-200 status."""
        mock_ollama = Mock()
        mock_ollama.status_code = 500
        mock_get.return_value = mock_ollama

        response = client.get("/api/health")

        assert response.status_code == 503

# ============================================================================
# MODELS ENDPOINT TESTS
# ============================================================================

class TestModelsEndpoint:
    """Tests for GET /api/models endpoint."""

    @patch('main.requests.get')
    def test_get_models_success(self, mock_get, client):
        """Test successful retrieval of available models."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "tinyllama:latest"},
                {"name": "llama2:7b"}
            ]
        }
        mock_get.return_value = mock_response

        response = client.get("/api/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "tinyllama:latest" in data["models"]
        assert data["current_model"] == Config.MODEL_NAME
        assert data["available"] is True

    @patch('main.requests.get')
    def test_get_models_empty_list(self, mock_get, client):
        """Test retrieval when no models are installed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        response = client.get("/api/models")

        assert response.status_code == 200
        data = response.json()
        assert data["models"] == []
        assert data["available"] is True

    @patch('main.requests.get')
    def test_get_models_connection_error(self, mock_get, client):
        """Test models endpoint when Ollama is unreachable."""
        mock_get.side_effect = ConnectionError("Connection refused")

        response = client.get("/api/models")

        assert response.status_code == 503

    @patch('main.requests.get')
    def test_get_models_request_error(self, mock_get, client):
        """Test models endpoint with general request error."""
        mock_get.side_effect = requests.RequestException("Network error")

        response = client.get("/api/models")

        assert response.status_code == 503

# ============================================================================
# CHAT ENDPOINT TESTS
# ============================================================================

class TestChatEndpoint:
    """Tests for POST /api/chat endpoint."""

    @patch('main.requests.post')
    def test_chat_success_streaming(self, mock_post, client):
        """Test successful streaming chat response."""
        # Mock Ollama response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            '{"response": "Hello"}',
            '{"response": " world"}',
            '{"response": "!"}',
        ]
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": True
        })

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @patch('main.requests.post')
    def test_chat_success_buffered(self, mock_post, client):
        """Test successful buffered (non-streaming) chat response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Hello! How can I help?"
        }
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": False
        })

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["model"] == Config.MODEL_NAME
        assert data["stream"] is False

    def test_chat_empty_message(self, client):
        """Test that empty message is rejected."""
        response = client.post("/api/chat", json={
            "message": "",
            "stream": True
        })

        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()

    def test_chat_whitespace_only_message(self, client):
        """Test that whitespace-only message is rejected."""
        response = client.post("/api/chat", json={
            "message": "   ",
            "stream": True
        })

        assert response.status_code == 400

    def test_chat_message_too_long(self, client):
        """Test that overly long message is rejected."""
        long_message = "x" * 4001

        response = client.post("/api/chat", json={
            "message": long_message,
            "stream": True
        })

        assert response.status_code == 400

    def test_chat_invalid_json(self, client):
        """Test handling of invalid JSON in request."""
        response = client.post("/api/chat", content="not json", headers={
            "Content-Type": "application/json"
        })

        assert response.status_code == 400

    @patch('main.requests.post')
    def test_chat_ollama_connection_error(self, mock_post, client):
        """Test chat when Ollama is unreachable."""
        mock_post.side_effect = ConnectionError("Connection refused")

        response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": True
        })

        assert response.status_code == 503

    @patch('main.requests.post')
    def test_chat_ollama_timeout(self, mock_post, client):
        """Test chat with timeout during Ollama request."""
        mock_post.side_effect = Timeout("Request timeout")

        response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": True
        })

        assert response.status_code == 503

    @patch('main.requests.post')
    def test_chat_ollama_error_response(self, mock_post, client):
        """Test handling of error response from Ollama."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Model not found"
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": True
        })

        assert response.status_code == 500

    @patch('main.requests.post')
    def test_chat_message_with_special_characters(self, mock_post, client):
        """Test chat with special characters and unicode."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = ['{"response": "Response"}']
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Hello 👋 world! 你好",
            "stream": True
        })

        assert response.status_code == 200

    def test_chat_missing_message_field(self, client):
        """Test handling of missing 'message' field."""
        response = client.post("/api/chat", json={
            "stream": True
        })

        assert response.status_code == 400

# ============================================================================
# APPLICATION INFO ENDPOINT TESTS
# ============================================================================

class TestInfoEndpoint:
    """Tests for GET /api/info endpoint."""

    def test_get_info(self, client):
        """Test retrieval of application information."""
        response = client.get("/api/info")

        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "version" in data
        assert "model" in data
        assert "description" in data
        assert "ollama_url" in data
        assert data["model"] == Config.MODEL_NAME

# ============================================================================
# UI SERVING ENDPOINT TESTS
# ============================================================================

class TestUIEndpoint:
    """Tests for GET / endpoint."""

    def test_serve_root(self, client):
        """Test serving the root UI page."""
        response = client.get("/")

        # Will be 404 if index.html doesn't exist, 200 if it does
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            assert response.headers["content-type"] == "text/html; charset=utf-8"

# ============================================================================
# API ROOT ENDPOINT TESTS
# ============================================================================

class TestAPIRootEndpoint:
    """Tests for GET /api/ endpoint."""

    def test_api_root(self, client):
        """Test API root information endpoint."""
        response = client.get("/api/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "health" in data["endpoints"]
        assert "chat" in data["endpoints"]

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    @patch('main.requests.get')
    @patch('main.requests.post')
    def test_complete_chat_workflow(self, mock_post, mock_get, client):
        """Test a complete chat workflow: health check -> chat."""
        # Setup mocks
        mock_health = Mock()
        mock_health.status_code = 200
        mock_health.json.return_value = {"models": []}
        mock_get.return_value = mock_health

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = ['{"response": "Hi there"}']
        mock_post.return_value = mock_response

        # Check health
        health_response = client.get("/api/health")
        assert health_response.status_code == 200

        # Send chat message
        chat_response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": True
        })
        assert chat_response.status_code == 200

    @patch('main.requests.get')
    @patch('main.requests.post')
    def test_degraded_service_workflow(self, mock_post, mock_get, client):
        """Test workflow when Ollama becomes unavailable."""
        # Setup mocks for failure
        mock_get.side_effect = ConnectionError()
        mock_post.side_effect = ConnectionError()

        # Health check should fail
        health_response = client.get("/api/health")
        assert health_response.status_code == 503

        # Chat should fail
        chat_response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": True
        })
        assert chat_response.status_code == 503

# ============================================================================
# TEST EXECUTION
# ============================================================================

# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestConfigurationManagement:
    """Tests for application configuration management."""

    def test_config_defaults(self):
        """Test that Config class has proper default values."""
        assert Config.MODEL_NAME == "tinyllama"
        assert Config.API_PORT == 8000
        assert Config.API_HOST == "0.0.0.0"
        assert 0.0 <= Config.TEMPERATURE <= 1.0
        assert 0.0 <= Config.TOP_P <= 1.0
        assert Config.TOP_K >= 0
        assert Config.OLLAMA_TIMEOUT > 0
        assert Config.HEALTH_CHECK_TIMEOUT > 0

    def test_config_ollama_url(self):
        """Test that Ollama URL is properly configured."""
        assert "localhost" in Config.OLLAMA_API_URL or "127.0.0.1" in Config.OLLAMA_API_URL
        assert "11434" in Config.OLLAMA_API_URL or "http" in Config.OLLAMA_API_URL

    def test_config_app_metadata(self):
        """Test application metadata in configuration."""
        assert Config.APP_NAME == "Ollama Chat Application"
        assert len(Config.APP_VERSION) > 0
        assert Config.APP_VERSION[0].isdigit()

# ============================================================================
# STREAMING RESPONSE TESTS
# ============================================================================

class TestStreamingResponses:
    """Tests for streaming response handling."""

    @patch('main.requests.post')
    def test_chat_streaming_empty_response(self, mock_post, client):
        """Test streaming with empty response lines."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            '{"response": ""}',
            '{"response": " "}',
        ]
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Test",
            "stream": True
        })

        assert response.status_code == 200

    @patch('main.requests.post')
    def test_chat_streaming_multiple_lines(self, mock_post, client):
        """Test streaming with many response lines."""
        mock_response = Mock()
        mock_response.status_code = 200
        lines = ['{"response": "word' + str(i) + '"}' for i in range(50)]
        mock_response.iter_lines.return_value = lines
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Test",
            "stream": True
        })

        assert response.status_code == 200

    @patch('main.requests.post')
    def test_chat_streaming_json_parse_error(self, mock_post, client):
        """Test handling of malformed JSON in streaming response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            'invalid json',
            '{"response": "recovered"}',
        ]
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Test",
            "stream": True
        })

        assert response.status_code == 200

# ============================================================================
# ERROR MESSAGE TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for comprehensive error handling."""

    @patch('main.requests.post')
    def test_chat_request_exception_general(self, mock_post, client):
        """Test general RequestException handling."""
        mock_post.side_effect = requests.RequestException("Generic error")

        response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": True
        })

        assert response.status_code == 503
        assert "error" in response.json()

    @patch('main.requests.get')
    def test_models_timeout(self, mock_get, client):
        """Test timeout in models endpoint."""
        mock_get.side_effect = Timeout("Timeout")

        response = client.get("/api/models")

        assert response.status_code == 503

    def test_validation_message_boundaries(self):
        """Test message validation at exact boundaries."""
        # Test message with exactly 4000 characters
        msg_4000 = "a" * 4000
        assert validate_message(msg_4000) == msg_4000

        # Test message with special chars at boundary
        msg_special = "a" * 3999 + "😀"
        assert len(validate_message(msg_special)) <= 4000

# ============================================================================
# PARAMETER VALIDATION TESTS
# ============================================================================

class TestParameterValidation:
    """Tests for parameter validation and edge cases."""

    @patch('main.requests.post')
    def test_chat_with_all_parameters(self, mock_post, client):
        """Test chat endpoint with all optional parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = ['{"response": "OK"}']
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Hello world",
            "stream": True,
            "temperature": 0.5,
            "top_p": 0.9,
            "top_k": 40
        })

        assert response.status_code == 200

    @patch('main.requests.post')
    def test_chat_with_default_parameters(self, mock_post, client):
        """Test chat with minimal required parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "OK"}
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Hello"
        })

        assert response.status_code == 200

# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and corner scenarios."""

    def test_message_with_only_numbers(self):
        """Test validation of numeric-only messages."""
        result = validate_message("12345")
        assert result == "12345"

    def test_message_with_only_punctuation(self):
        """Test validation of punctuation-only messages."""
        result = validate_message("!@#$%")
        assert result == "!@#$%"

    def test_message_with_newlines_and_tabs(self):
        """Test handling of whitespace characters."""
        msg = "line1\nline2\tindented"
        result = validate_message(msg)
        assert "\n" in result
        assert "\t" in result

    @patch('main.requests.post')
    def test_chat_with_very_long_model_response(self, mock_post, client):
        """Test handling of very long model responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        long_lines = ['{"response": "' + "x" * 1000 + '"}' for _ in range(5)]
        mock_response.iter_lines.return_value = long_lines
        mock_post.return_value = mock_response

        response = client.post("/api/chat", json={
            "message": "Test",
            "stream": True
        })

        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
