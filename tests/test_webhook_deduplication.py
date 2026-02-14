"""
Integration test for webhook deduplication in main.py

Tests the webhook endpoint's deduplication logic.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.message_cache import clear_cache


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_cache_before_test():
    """Clean the message cache before each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def mock_bot_handler():
    """Mock the handle_telegram_update function to avoid external calls."""
    with patch('src.main.handle_telegram_update', new_callable=AsyncMock) as mock:
        # Return a successful response by default
        mock.return_value = {"ok": True}
        yield mock


@pytest.fixture
def mock_throttle():
    """Mock the message throttling to process messages immediately in tests."""
    with patch('src.main.has_pending_reply') as mock_has_pending, \
         patch('src.main.get_pending_messages') as mock_get_pending:
        # No pending messages by default - allow processing
        mock_has_pending.return_value = False
        mock_get_pending.return_value = []
        yield (mock_has_pending, mock_get_pending)


@pytest.mark.integration
class TestWebhookDeduplication:
    """Integration tests for webhook message deduplication."""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint works."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_webhook_with_duplicate_message_skips_second(self, client, mock_bot_handler, mock_throttle):
        """Test that duplicate messages are skipped."""
        # Create a mock webhook payload
        webhook_data = {
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
        
        # First request should be processed
        response1 = client.post("/webhook", json=webhook_data)
        assert response1.status_code == 200
        result1 = response1.json()
        assert result1.get("ok") is True
        assert result1.get("skipped") != "duplicate"
        assert mock_bot_handler.call_count == 1
        
        # Second request with same message_id should be skipped
        response2 = client.post("/webhook", json=webhook_data)
        assert response2.status_code == 200
        result2 = response2.json()
        assert result2.get("ok") is True
        assert result2.get("skipped") == "duplicate"
        # Bot handler should not be called again
        assert mock_bot_handler.call_count == 1
    
    def test_webhook_different_messages_not_skipped(self, client, mock_bot_handler, mock_throttle):
        """Test that different messages are not skipped."""
        # First message
        webhook_data1 = {
            "message": {
                "message_id": 12345,
                "from": {
                    "id": 123456789
                },
                "chat": {
                    "id": 123456789
                },
                "text": "First message"
            }
        }
        
        # Second message with different ID
        webhook_data2 = {
            "message": {
                "message_id": 67890,
                "from": {
                    "id": 123456789
                },
                "chat": {
                    "id": 123456789
                },
                "text": "Second message"
            }
        }
        
        # Both should be processed, not skipped
        response1 = client.post("/webhook", json=webhook_data1)
        assert response1.status_code == 200
        result1 = response1.json()
        assert result1.get("ok") is True
        assert result1.get("skipped") != "duplicate"
        
        response2 = client.post("/webhook", json=webhook_data2)
        assert response2.status_code == 200
        result2 = response2.json()
        assert result2.get("ok") is True
        assert result2.get("skipped") != "duplicate"
        
        # Bot handler should be called twice
        assert mock_bot_handler.call_count == 2
    
    def test_webhook_same_message_id_different_users(self, client, mock_bot_handler, mock_throttle):
        """Test that same message ID from different users are not skipped."""
        # First user
        webhook_data1 = {
            "message": {
                "message_id": 12345,
                "from": {
                    "id": 111111111
                },
                "chat": {
                    "id": 111111111
                },
                "text": "Message from user 1"
            }
        }
        
        # Second user with same message ID
        webhook_data2 = {
            "message": {
                "message_id": 12345,
                "from": {
                    "id": 222222222
                },
                "chat": {
                    "id": 222222222
                },
                "text": "Message from user 2"
            }
        }
        
        # Both should be processed
        response1 = client.post("/webhook", json=webhook_data1)
        assert response1.status_code == 200
        result1 = response1.json()
        assert result1.get("ok") is True
        assert result1.get("skipped") != "duplicate"
        
        response2 = client.post("/webhook", json=webhook_data2)
        assert response2.status_code == 200
        result2 = response2.json()
        assert result2.get("ok") is True
        assert result2.get("skipped") != "duplicate"
        
        # Bot handler should be called twice
        assert mock_bot_handler.call_count == 2
    
    def test_webhook_missing_message_id(self, client, mock_bot_handler, mock_throttle):
        """Test that webhook handles missing message_id gracefully."""
        # Webhook data without message_id
        webhook_data = {
            "message": {
                "from": {
                    "id": 123456789
                },
                "chat": {
                    "id": 123456789
                },
                "text": "Message without ID"
            }
        }
        
        # Should not crash, will process normally without deduplication
        response = client.post("/webhook", json=webhook_data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("ok") is True
        assert result.get("error") is None
        assert mock_bot_handler.call_count == 1
    
    def test_webhook_missing_user_id(self, client, mock_bot_handler, mock_throttle):
        """Test that webhook handles missing user ID gracefully."""
        # Webhook data without from.id
        webhook_data = {
            "message": {
                "message_id": 12345,
                "chat": {
                    "id": 123456789
                },
                "text": "Message without user ID"
            }
        }
        
        # Should not crash
        response = client.post("/webhook", json=webhook_data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("ok") is True
        assert result.get("error") is None
        assert mock_bot_handler.call_count == 1
    
    def test_webhook_bot_handler_error_returns_error(self, client, mock_bot_handler, mock_throttle):
        """Test that errors from bot handler are properly reported."""
        # Make bot handler raise an exception
        mock_bot_handler.side_effect = Exception("Bot processing failed")
        
        webhook_data = {
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
        
        response = client.post("/webhook", json=webhook_data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("ok") is False
        assert result.get("error") == "Internal server error"
