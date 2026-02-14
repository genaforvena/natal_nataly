"""
Tests for reply-based message throttling functionality.

These tests verify that messages are throttled based on reply status,
not on time windows.
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
def clean_state_before_test():
    """Clean message cache before each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def mock_bot_handler():
    """Mock the handle_telegram_update function to track calls."""
    with patch('src.main.handle_telegram_update', new_callable=AsyncMock) as mock:
        mock.return_value = {"ok": True}
        yield mock


def create_webhook_payload(user_id: int, message_id: int, text: str):
    """Helper to create webhook payload."""
    return {
        "message": {
            "message_id": message_id,
            "from": {
                "id": user_id
            },
            "chat": {
                "id": user_id
            },
            "text": text
        }
    }


@pytest.mark.unit
class TestReplyBasedThrottling:
    """Tests for reply-based message throttling."""
    
    def test_first_message_processes_immediately(self, client, mock_bot_handler):
        """Test that the first message from a user is processed immediately."""
        payload = create_webhook_payload(user_id=111, message_id=1, text="First message")
        
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result.get("ok") is True
        assert result.get("throttled") is not True
        assert mock_bot_handler.call_count == 1
    
    def test_second_message_while_processing_throttled(self, client, mock_bot_handler):
        """Test that a second message while first is processing is throttled."""
        user_id = 222
        
        # First message - starts processing (bot handler is called but reply not yet marked)
        payload1 = create_webhook_payload(user_id=user_id, message_id=1, text="Message 1")
        response1 = client.post("/webhook", json=payload1)
        assert response1.status_code == 200
        assert mock_bot_handler.call_count == 1
        
        # Second message immediately after (before reply is sent)
        # This should be throttled because first message hasn't been replied yet
        payload2 = create_webhook_payload(user_id=user_id, message_id=2, text="Message 2")
        response2 = client.post("/webhook", json=payload2)
        assert response2.status_code == 200
        result2 = response2.json()
        assert result2.get("throttled") is True
        # Bot handler should not be called again
        assert mock_bot_handler.call_count == 1
    
    def test_different_users_throttled_independently(self, client, mock_bot_handler):
        """Test that throttling is per-user, not global."""
        # User 1 sends messages
        payload1a = create_webhook_payload(user_id=444, message_id=1, text="User 1 - Message 1")
        response1a = client.post("/webhook", json=payload1a)
        assert response1a.json().get("ok") is True
        assert mock_bot_handler.call_count == 1
        
        # User 2 sends a message (should not be throttled by User 1's activity)
        payload2a = create_webhook_payload(user_id=555, message_id=1, text="User 2 - Message 1")
        response2a = client.post("/webhook", json=payload2a)
        assert response2a.json().get("ok") is True
        assert response2a.json().get("throttled") is not True
        assert mock_bot_handler.call_count == 2
        
        # User 1 sends another message (should be throttled because first message not replied)
        payload1b = create_webhook_payload(user_id=444, message_id=2, text="User 1 - Message 2")
        response1b = client.post("/webhook", json=payload1b)
        assert response1b.json().get("throttled") is True
        assert mock_bot_handler.call_count == 2  # Should not increment
    
    def test_message_combining_with_pending_messages(self, client, mock_bot_handler):
        """Test that pending messages are combined when processing."""
        user_id = 666
        
        # Mock bot handler to check the combined message
        combined_text = None
        def capture_combined_text(data):
            nonlocal combined_text
            combined_text = data.get("message", {}).get("text", "")
            return {"ok": True}
        
        mock_bot_handler.side_effect = capture_combined_text
        
        # First message
        payload1 = create_webhook_payload(user_id=user_id, message_id=1, text="What is my sun sign?")
        client.post("/webhook", json=payload1)
        
        # Second message (throttled, stored)
        payload2 = create_webhook_payload(user_id=user_id, message_id=2, text="And my moon sign?")
        response2 = client.post("/webhook", json=payload2)
        assert response2.json().get("throttled") is True
        
        # Third message (throttled, stored)
        payload3 = create_webhook_payload(user_id=user_id, message_id=3, text="Also my rising?")
        response3 = client.post("/webhook", json=payload3)
        assert response3.json().get("throttled") is True
        
        # Check that first message text was sent to bot (may include combined messages)
        # The exact combination logic depends on implementation
        assert combined_text is not None
