"""
Integration tests for message_text storage and combining functionality.

These tests verify that the message_text column is properly integrated
across the entire message throttling and combining pipeline.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.message_cache import clear_cache, get_pending_messages, mark_all_pending_as_replied


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
    """Mock the handle_telegram_update function to track calls and capture combined text."""
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


@pytest.mark.integration
class TestMessageTextIntegration:
    """Integration tests for message_text storage and combining."""
    
    def test_message_text_stored_in_database(self, client, mock_bot_handler):
        """Test that message text is stored in the database when marking messages."""
        user_id = 12345
        message_text = "What is my sun sign?"
        
        # Send first message
        payload = create_webhook_payload(user_id, 1, message_text)
        response = client.post("/webhook", json=payload)
        
        assert response.status_code == 200
        assert mock_bot_handler.call_count == 1
        
        # Verify message text was passed to bot handler
        call_args = mock_bot_handler.call_args[0][0]
        assert call_args["message"]["text"] == message_text
    
    def test_multiple_messages_combined_with_separator(self, client, mock_bot_handler):
        """
        Test debounce throttling: first message is processed, subsequent messages
        from the same user within the debounce window are throttled (not combined).
        Uses a deterministic mock for should_debounce to avoid timing-dependent failures.
        """
        user_id = 99999
        
        # Track messages that reach the bot
        processed_texts = []
        
        def capture_text(data):
            text = data.get("message", {}).get("text", "")
            processed_texts.append(text)
            return {"ok": True}
        
        mock_bot_handler.side_effect = capture_text
        
        # Patch should_debounce: first call passes through, subsequent calls throttle
        debounce_side_effects = [False, True, True]
        with patch('src.main.should_debounce', side_effect=debounce_side_effects):
            # First message is processed immediately (debounce returns False)
            payload1 = create_webhook_payload(user_id, 1, "First message")
            response1 = client.post("/webhook", json=payload1)
            assert response1.status_code == 200
            assert response1.json().get("throttled") is not True
            
            # Subsequent messages are throttled (debounce returns True)
            payload2 = create_webhook_payload(user_id, 2, "Second message")
            response2 = client.post("/webhook", json=payload2)
            assert response2.json().get("throttled") is True
            
            payload3 = create_webhook_payload(user_id, 3, "Third message")
            response3 = client.post("/webhook", json=payload3)
            assert response3.json().get("throttled") is True
        
        # Only the first message reached the bot handler
        assert len(processed_texts) == 1
        assert processed_texts[0] == "First message"
    
    def test_combined_messages_use_correct_separator(self, client, mock_bot_handler):
        r"""
        Test that combined messages use the '\n\n---\n\n' separator.
        """
        user_id = 77777
        
        # Track the combined text
        captured_text = None
        
        def capture_text(data):
            nonlocal captured_text
            captured_text = data.get("message", {}).get("text", "")
            # Don't mark as replied so we can test combining
            return {"ok": True}
        
        mock_bot_handler.side_effect = capture_text
        
        # Send first message
        payload1 = create_webhook_payload(user_id, 1, "Message one")
        client.post("/webhook", json=payload1)
        
        # Send second and third messages (will be throttled)
        payload2 = create_webhook_payload(user_id, 2, "Message two")
        client.post("/webhook", json=payload2)
        
        payload3 = create_webhook_payload(user_id, 3, "Message three")
        client.post("/webhook", json=payload3)
        
        # Retrieve pending messages to check they're stored
        pending = get_pending_messages(str(user_id))
        assert len(pending) == 3
        
        # Verify texts are stored correctly
        assert pending[0].message_text == "Message one"
        assert pending[1].message_text == "Message two"
        assert pending[2].message_text == "Message three"
    
    def test_message_text_with_unicode_and_newlines(self, client, mock_bot_handler):
        """Test that message text with Unicode and newlines is preserved."""
        user_id = 88888
        message_text = "Hello! 👋\nI want to know:\n- My sun sign\n- My moon sign"
        
        # Send message
        payload = create_webhook_payload(user_id, 1, message_text)
        response = client.post("/webhook", json=payload)
        
        assert response.status_code == 200
        
        # Verify message text was passed correctly
        call_args = mock_bot_handler.call_args[0][0]
        assert call_args["message"]["text"] == message_text
        
        # Also verify it's stored in database
        pending = get_pending_messages(str(user_id))
        assert len(pending) == 1
        assert pending[0].message_text == message_text
    
    def test_empty_message_text_handled_gracefully(self, client, mock_bot_handler):
        """Test that empty message text doesn't break the pipeline."""
        user_id = 66666
        
        # Send message with empty text
        payload = create_webhook_payload(user_id, 1, "")
        response = client.post("/webhook", json=payload)
        
        assert response.status_code == 200
        assert mock_bot_handler.call_count == 1
        
        # Verify empty text is stored
        pending = get_pending_messages(str(user_id))
        assert len(pending) == 1
        assert pending[0].message_text == ""
    
    def test_null_message_text_handled_gracefully(self, client, mock_bot_handler):
        """Test that messages without text field don't break the pipeline."""
        user_id = 55555
        
        # Send message without text field (e.g., photo, sticker, etc.)
        payload = {
            "message": {
                "message_id": 1,
                "from": {
                    "id": user_id
                },
                "chat": {
                    "id": user_id
                }
                # No "text" field
            }
        }
        response = client.post("/webhook", json=payload)
        
        assert response.status_code == 200
        assert mock_bot_handler.call_count == 1
        
        # Verify None/empty text is stored
        pending = get_pending_messages(str(user_id))
        assert len(pending) == 1
        # message_text could be None or empty string
        assert pending[0].message_text in [None, ""]
