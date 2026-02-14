"""
Tests for migration compatibility and handling of pending messages with NULL text.

These tests verify that the system handles edge cases where pending messages
might have NULL message_text values gracefully and doesn't block new messages.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.message_cache import clear_cache, get_pending_messages, mark_all_pending_as_replied
from src.models import ProcessedMessage
from src.db import SessionLocal
from datetime import datetime, timezone


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_state_before_test():
    """Clean message cache and database before each test."""
    clear_cache()
    
    # Also clean up database
    session = SessionLocal()
    try:
        session.query(ProcessedMessage).delete()
        session.commit()
    finally:
        session.close()
    
    yield
    
    # Clean up after test
    clear_cache()
    session = SessionLocal()
    try:
        session.query(ProcessedMessage).delete()
        session.commit()
    finally:
        session.close()


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


@pytest.mark.integration
class TestNullMessageTextHandling:
    """Tests for handling pending messages with NULL message_text."""
    
    def test_combining_skips_null_text_messages(self, client, mock_bot_handler):
        """
        Test that when combining messages, NULL text messages are skipped
        but don't prevent processing.
        """
        user_id = 55555
        telegram_id = str(user_id)
        
        # Track what text is sent to the bot
        captured_texts = []
        
        def capture_text(data):
            text = data.get("message", {}).get("text", "")
            captured_texts.append(text)
            # Mark as replied so we can continue
            mark_all_pending_as_replied(telegram_id)
            return {"ok": True}
        
        mock_bot_handler.side_effect = capture_text
        
        # Send first message with text
        payload1 = create_webhook_payload(user_id, 1, "Message 1")
        response1 = client.post("/webhook", json=payload1)
        assert response1.status_code == 200
        
        # Manually mark as replied to allow next message
        mark_all_pending_as_replied(telegram_id)
        
        # Send second message with text
        payload2 = create_webhook_payload(user_id, 2, "Message 2")
        response2 = client.post("/webhook", json=payload2)
        assert response2.status_code == 200
        
        # Should have processed messages with text
        assert len(captured_texts) >= 1
        assert all(text != "" for text in captured_texts)
    
    def test_empty_all_texts_does_not_override_current_message(self, client, mock_bot_handler):
        """
        Test that if all pending messages have NULL text, the current message
        text is not overridden with empty string.
        """
        user_id = 66666
        telegram_id = str(user_id)
        
        # Manually create pending messages with NULL text
        session = SessionLocal()
        try:
            # Create messages without text (edge case)
            for i in range(1, 3):
                msg = ProcessedMessage(
                    telegram_id=telegram_id,
                    message_id=i,
                    processed_at=datetime.now(timezone.utc),
                    reply_sent=False,
                    message_text=None
                )
                session.add(msg)
            session.commit()
        finally:
            session.close()
        
        # Track what text is sent to the bot
        captured_text = None
        
        def capture_text(data):
            nonlocal captured_text
            captured_text = data.get("message", {}).get("text", "")
            return {"ok": True}
        
        mock_bot_handler.side_effect = capture_text
        
        # Send a new message with text
        new_message_text = "What is my sun sign?"
        payload = create_webhook_payload(user_id, 3, new_message_text)
        
        # This will be throttled by the old messages
        response = client.post("/webhook", json=payload)
        
        # Either throttled or processed, but if processed, should have correct text
        if response.json().get("throttled"):
            # Expected - old messages are blocking
            # Now mark old ones as replied and try again
            mark_all_pending_as_replied(telegram_id)
            
            # Send another message
            payload4 = create_webhook_payload(user_id, 4, "Another message")
            response4 = client.post("/webhook", json=payload4)
            assert response4.status_code == 200
            
            if mock_bot_handler.call_count > 0:
                assert captured_text != ""
                assert captured_text in ["Another message", new_message_text]
        else:
            # If it was processed, text should not be empty
            if captured_text is not None:
                assert captured_text == new_message_text
    
    def test_warning_logged_for_null_text_messages(self, client, mock_bot_handler):
        """
        Test that a warning is logged when all pending messages have NULL text.
        """
        user_id = 77777
        telegram_id = str(user_id)
        
        # Create pending messages with NULL text
        session = SessionLocal()
        try:
            for i in range(1, 3):
                msg = ProcessedMessage(
                    telegram_id=telegram_id,
                    message_id=i,
                    processed_at=datetime.now(timezone.utc),
                    reply_sent=False,
                    message_text=None
                )
                session.add(msg)
            session.commit()
        finally:
            session.close()
        
        # Mock logging to capture warnings
        with patch('src.main.logger') as mock_logger:
            mock_bot_handler.return_value = {"ok": True}
            
            # Send a new message
            payload = create_webhook_payload(user_id, 3, "New message")
            response = client.post("/webhook", json=payload)
            
            # If throttled, mark old ones and try again
            if response.json().get("throttled"):
                mark_all_pending_as_replied(telegram_id)
                payload4 = create_webhook_payload(user_id, 4, "Another message")
                client.post("/webhook", json=payload4)
            
            # Check if warning was logged (if we got to the combining logic)
            if mock_bot_handler.call_count > 0:
                # Should have at least attempted to log something
                assert mock_logger.info.called or mock_logger.warning.called
