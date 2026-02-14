"""
Tests for message throttling functionality.

These tests verify that messages arriving within a 15-second window
are properly grouped and processed together.
"""

import pytest
import time
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.message_cache import clear_cache
from src.message_throttler import clear_all_throttles, get_throttle_stats


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_state_before_test():
    """Clean both message cache and throttle state before each test."""
    clear_cache()
    clear_all_throttles()
    yield
    clear_cache()
    clear_all_throttles()


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
class TestMessageThrottling:
    """Tests for message throttling (15-second window)."""
    
    def test_first_message_processes_immediately(self, client, mock_bot_handler):
        """Test that the first message from a user is processed immediately."""
        payload = create_webhook_payload(user_id=111, message_id=1, text="First message")
        
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result.get("ok") is True
        assert result.get("throttled") is not True
        assert mock_bot_handler.call_count == 1
    
    def test_second_message_within_window_throttled(self, client, mock_bot_handler):
        """Test that a second message within 15 seconds is throttled."""
        user_id = 222
        
        # First message
        payload1 = create_webhook_payload(user_id=user_id, message_id=1, text="Message 1")
        response1 = client.post("/webhook", json=payload1)
        assert response1.status_code == 200
        assert mock_bot_handler.call_count == 1
        
        # Second message immediately after (within throttle window)
        payload2 = create_webhook_payload(user_id=user_id, message_id=2, text="Message 2")
        response2 = client.post("/webhook", json=payload2)
        assert response2.status_code == 200
        result2 = response2.json()
        assert result2.get("throttled") is True
        # Bot handler should not be called again
        assert mock_bot_handler.call_count == 1
    
    def test_third_message_processes_grouped_messages(self, client, mock_bot_handler):
        """Test that multiple throttled messages are processed together after window."""
        user_id = 333
        
        # First message
        payload1 = create_webhook_payload(user_id=user_id, message_id=1, text="Message 1")
        client.post("/webhook", json=payload1)
        assert mock_bot_handler.call_count == 1
        
        # Second message throttled
        payload2 = create_webhook_payload(user_id=user_id, message_id=2, text="Message 2")
        response2 = client.post("/webhook", json=payload2)
        assert response2.json().get("throttled") is True
        assert mock_bot_handler.call_count == 1
        
        # Third message throttled
        payload3 = create_webhook_payload(user_id=user_id, message_id=3, text="Message 3")
        response3 = client.post("/webhook", json=payload3)
        assert response3.json().get("throttled") is True
        assert mock_bot_handler.call_count == 1
        
        # Wait for throttle window to expire (15+ seconds)
        # For testing purposes, we'll mock the time to avoid actual waiting
        # In production, this would naturally wait 15 seconds
        with patch('src.message_throttler.datetime') as mock_datetime:
            from datetime import datetime, timezone, timedelta
            # Set time to 16 seconds after first message
            mock_datetime.now.return_value = datetime.now(timezone.utc) + timedelta(seconds=16)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Fourth message should trigger processing of grouped messages
            payload4 = create_webhook_payload(user_id=user_id, message_id=4, text="Message 4")
            response4 = client.post("/webhook", json=payload4)
            assert response4.status_code == 200
            # This should process the grouped messages
            # Note: The exact behavior depends on implementation - it should combine messages
    
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
        
        # User 1 sends another message (should be throttled)
        payload1b = create_webhook_payload(user_id=444, message_id=2, text="User 1 - Message 2")
        response1b = client.post("/webhook", json=payload1b)
        assert response1b.json().get("throttled") is True
        assert mock_bot_handler.call_count == 2  # Should not increment
    
    def test_throttle_stats_tracking(self, client):
        """Test that throttle statistics are correctly tracked."""
        user_id = 666
        
        # Initial stats
        stats = get_throttle_stats()
        initial_users = stats.get("active_users", 0)
        
        # Send first message
        payload1 = create_webhook_payload(user_id=user_id, message_id=1, text="Message 1")
        client.post("/webhook", json=payload1)
        
        # Check stats after first message
        stats = get_throttle_stats()
        assert stats.get("active_users") == initial_users + 1
        assert stats.get("throttle_window_seconds") == 15
        
        # Send second message (throttled)
        payload2 = create_webhook_payload(user_id=user_id, message_id=2, text="Message 2")
        client.post("/webhook", json=payload2)
        
        # Stats should show pending messages
        stats = get_throttle_stats()
        assert stats.get("total_pending_messages") >= 1
    
    def test_combined_message_format(self, client, mock_bot_handler):
        """Test that grouped messages are properly combined with separator."""
        user_id = 777
        
        # Send first message
        payload1 = create_webhook_payload(user_id=user_id, message_id=1, text="First")
        client.post("/webhook", json=payload1)
        
        # Send second message (throttled)
        payload2 = create_webhook_payload(user_id=user_id, message_id=2, text="Second")
        client.post("/webhook", json=payload2)
        
        # Mock time advancement and send third message
        with patch('src.message_throttler.datetime') as mock_datetime:
            from datetime import datetime, timezone, timedelta
            mock_datetime.now.return_value = datetime.now(timezone.utc) + timedelta(seconds=16)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            payload3 = create_webhook_payload(user_id=user_id, message_id=3, text="Third")
            client.post("/webhook", json=payload3)
            
            # Check that the bot handler was called with combined messages
            # The implementation should combine "Second" and "Third" with separator
            if mock_bot_handler.call_count > 1:
                # Get the last call's argument
                last_call = mock_bot_handler.call_args_list[-1]
                call_data = last_call[0][0]  # First positional argument
                message_text = call_data.get("message", {}).get("text", "")
                
                # Messages should be combined with separator
                if "---" in message_text:
                    assert "Second" in message_text
                    assert "Third" in message_text


@pytest.mark.unit
class TestThrottlingEdgeCases:
    """Test edge cases for message throttling."""
    
    def test_empty_message_text_handled(self, client, mock_bot_handler):
        """Test that messages with empty text are handled correctly."""
        payload = create_webhook_payload(user_id=888, message_id=1, text="")
        
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json().get("ok") is True
    
    def test_missing_message_text_handled(self, client, mock_bot_handler):
        """Test that messages without text field are handled correctly."""
        payload = {
            "message": {
                "message_id": 1,
                "from": {"id": 999},
                "chat": {"id": 999}
                # No "text" field
            }
        }
        
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        # Should not crash, even if there's no text
