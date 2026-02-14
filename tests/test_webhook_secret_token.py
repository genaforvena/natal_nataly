"""
Tests for webhook secret token verification.

These tests verify that the webhook endpoint properly validates
the X-Telegram-Bot-Api-Secret-Token header when TELEGRAM_SECRET_TOKEN
environment variable is configured.
"""

import pytest
import os
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_bot_handler():
    """Mock the handle_telegram_update function to avoid external calls."""
    with patch('src.main.handle_telegram_update', new_callable=AsyncMock) as mock:
        mock.return_value = {"ok": True}
        yield mock


@pytest.fixture
def mock_dedup():
    """Mock the message deduplication to avoid database issues in tests."""
    with patch('src.main.mark_if_new') as mock:
        # Always return True (message is new) by default
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_throttle():
    """Mock the message throttling to avoid timing issues in tests."""
    with patch('src.main.should_process_message') as mock:
        # Always return (True, [message_text]) - process immediately with single message
        def side_effect(telegram_id, message_text):
            return (True, [message_text])
        mock.side_effect = side_effect
        yield mock


@pytest.fixture
def sample_webhook_data():
    """Standard webhook payload for testing."""
    return {
        "message": {
            "message_id": 12345,
            "from": {
                "id": 123456789
            },
            "chat": {
                "id": 123456789
            },
            "text": "Test message"
        }
    }


@pytest.mark.unit
class TestWebhookSecretToken:
    """Tests for webhook secret token verification."""
    
    def test_webhook_without_secret_token_env_accepts_any_request(self, client, mock_bot_handler, mock_dedup, mock_throttle, sample_webhook_data):
        """Test that webhook works normally when TELEGRAM_SECRET_TOKEN is not configured."""
        # Ensure no secret token is set
        with patch.dict(os.environ, {}, clear=False):
            if 'TELEGRAM_SECRET_TOKEN' in os.environ:
                del os.environ['TELEGRAM_SECRET_TOKEN']
            
            response = client.post("/webhook", json=sample_webhook_data)
            assert response.status_code == 200
            result = response.json()
            assert result.get("ok") is True
            assert mock_bot_handler.call_count == 1
    
    def test_webhook_with_secret_token_env_and_valid_header_succeeds(self, client, mock_bot_handler, mock_dedup, mock_throttle, sample_webhook_data):
        """Test that webhook accepts requests with valid secret token."""
        secret_token = "test_secret_token_12345"
        
        with patch.dict(os.environ, {"TELEGRAM_SECRET_TOKEN": secret_token}):
            response = client.post(
                "/webhook",
                json=sample_webhook_data,
                headers={"X-Telegram-Bot-Api-Secret-Token": secret_token}
            )
            assert response.status_code == 200
            result = response.json()
            assert result.get("ok") is True
            assert result.get("error") is None
            assert mock_bot_handler.call_count == 1
    
    def test_webhook_with_secret_token_env_and_invalid_header_rejects(self, client, mock_bot_handler, mock_dedup, mock_throttle, sample_webhook_data):
        """Test that webhook rejects requests with invalid secret token."""
        secret_token = "correct_secret_token"
        wrong_token = "wrong_secret_token"
        
        with patch.dict(os.environ, {"TELEGRAM_SECRET_TOKEN": secret_token}):
            response = client.post(
                "/webhook",
                json=sample_webhook_data,
                headers={"X-Telegram-Bot-Api-Secret-Token": wrong_token}
            )
            assert response.status_code == 200
            result = response.json()
            assert result.get("ok") is False
            assert result.get("error") == "Unauthorized"
            # Bot handler should not be called
            assert mock_bot_handler.call_count == 0
    
    def test_webhook_with_secret_token_env_and_missing_header_rejects(self, client, mock_bot_handler, mock_dedup, mock_throttle, sample_webhook_data):
        """Test that webhook rejects requests with missing secret token header."""
        secret_token = "required_secret_token"
        
        with patch.dict(os.environ, {"TELEGRAM_SECRET_TOKEN": secret_token}):
            # Don't include the header at all
            response = client.post("/webhook", json=sample_webhook_data)
            assert response.status_code == 200
            result = response.json()
            assert result.get("ok") is False
            assert result.get("error") == "Unauthorized"
            # Bot handler should not be called
            assert mock_bot_handler.call_count == 0
    
    def test_webhook_with_secret_token_env_and_empty_header_rejects(self, client, mock_bot_handler, mock_dedup, mock_throttle, sample_webhook_data):
        """Test that webhook rejects requests with empty secret token header."""
        secret_token = "required_secret_token"
        
        with patch.dict(os.environ, {"TELEGRAM_SECRET_TOKEN": secret_token}):
            response = client.post(
                "/webhook",
                json=sample_webhook_data,
                headers={"X-Telegram-Bot-Api-Secret-Token": ""}
            )
            assert response.status_code == 200
            result = response.json()
            assert result.get("ok") is False
            assert result.get("error") == "Unauthorized"
            # Bot handler should not be called
            assert mock_bot_handler.call_count == 0
    
    def test_webhook_secret_token_is_case_sensitive(self, client, mock_bot_handler, mock_dedup, mock_throttle, sample_webhook_data):
        """Test that secret token comparison is case-sensitive."""
        secret_token = "CaseSensitiveToken"
        wrong_case_token = "casesensitivetoken"
        
        with patch.dict(os.environ, {"TELEGRAM_SECRET_TOKEN": secret_token}):
            response = client.post(
                "/webhook",
                json=sample_webhook_data,
                headers={"X-Telegram-Bot-Api-Secret-Token": wrong_case_token}
            )
            assert response.status_code == 200
            result = response.json()
            assert result.get("ok") is False
            assert result.get("error") == "Unauthorized"
            assert mock_bot_handler.call_count == 0
    
    def test_webhook_secret_token_allows_special_characters(self, client, mock_bot_handler, mock_dedup, mock_throttle, sample_webhook_data):
        """Test that secret tokens with special characters work correctly."""
        secret_token = "token!@#$%^&*()_+-={}[]|:;<>?,./"
        
        with patch.dict(os.environ, {"TELEGRAM_SECRET_TOKEN": secret_token}):
            response = client.post(
                "/webhook",
                json=sample_webhook_data,
                headers={"X-Telegram-Bot-Api-Secret-Token": secret_token}
            )
            assert response.status_code == 200
            result = response.json()
            assert result.get("ok") is True
            assert mock_bot_handler.call_count == 1
    
    def test_backward_compatibility_empty_secret_token_env(self, client, mock_bot_handler, mock_dedup, mock_throttle, sample_webhook_data):
        """Test that empty TELEGRAM_SECRET_TOKEN env var disables verification."""
        with patch.dict(os.environ, {"TELEGRAM_SECRET_TOKEN": ""}):
            # No header provided
            response = client.post("/webhook", json=sample_webhook_data)
            assert response.status_code == 200
            result = response.json()
            assert result.get("ok") is True
            assert mock_bot_handler.call_count == 1
