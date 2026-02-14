"""
Tests for startup cleanup of stale pending messages.

This test verifies that pending messages from before application restart
are properly cleaned up on startup to prevent blocking new messages.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from src.main import app
from src.message_cache import clear_cache
from src.db import SessionLocal
from src.models import ProcessedMessage


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


@pytest.mark.unit
class TestStartupCleanup:
    """Tests for startup cleanup functionality."""
    
    def test_stale_pending_messages_cleaned_on_startup(self, client):
        """Test that stale pending messages are marked as replied on startup."""
        # Setup: Insert stale pending messages directly into DB
        # (simulating messages left pending from before restart)
        session = SessionLocal()
        try:
            # Create some old pending messages (simulating pre-restart state)
            old_time = datetime.now(timezone.utc) - timedelta(minutes=30)
            stale_messages = [
                ProcessedMessage(
                    telegram_id="140230022",
                    message_id=1900 + i,
                    processed_at=old_time,
                    reply_sent=False,
                    message_text=f"Old message {i}"
                )
                for i in range(6)
            ]
            
            session.add_all(stale_messages)
            session.commit()
            
            # Verify they're pending
            pending_count = session.query(ProcessedMessage).filter_by(
                telegram_id="140230022",
                reply_sent=False
            ).count()
            assert pending_count == 6
        finally:
            session.close()
        
        # Simulate application restart by creating new client
        # (this triggers startup event which should clean up stale messages)
        with TestClient(app) as new_client:
            # Verify that stale messages were marked as replied
            session = SessionLocal()
            try:
                pending_count = session.query(ProcessedMessage).filter_by(
                    telegram_id="140230022",
                    reply_sent=False
                ).count()
                
                # After startup, stale messages should be marked as replied
                assert pending_count == 0, "Stale pending messages should be cleaned up on startup"
                
                # Verify they were marked, not deleted
                total_count = session.query(ProcessedMessage).filter_by(
                    telegram_id="140230022"
                ).count()
                assert total_count == 6, "Messages should be marked, not deleted"
            finally:
                session.close()
    
    def test_new_messages_not_blocked_after_cleanup(self, client):
        """Test that new messages can be processed after stale message cleanup."""
        # Setup: Insert stale pending messages
        session = SessionLocal()
        try:
            old_time = datetime.now(timezone.utc) - timedelta(minutes=30)
            stale_message = ProcessedMessage(
                telegram_id="999999",
                message_id=1,
                processed_at=old_time,
                reply_sent=False,
                message_text="Old stale message"
            )
            session.add(stale_message)
            session.commit()
        finally:
            session.close()
        
        # Restart application (cleanup happens)
        with TestClient(app) as new_client:
            # Send a new message - should NOT be throttled because stale messages are cleaned
            from unittest.mock import patch, AsyncMock
            
            with patch('src.main.handle_telegram_update', new_callable=AsyncMock) as mock_bot:
                mock_bot.return_value = {"ok": True}
                
                payload = {
                    "message": {
                        "message_id": 2,
                        "from": {"id": 999999},
                        "chat": {"id": 999999},
                        "text": "New message after restart"
                    }
                }
                
                response = new_client.post("/webhook", json=payload)
                assert response.status_code == 200
                result = response.json()
                
                # Should NOT be throttled
                assert result.get("throttled") is not True
                assert mock_bot.call_count == 1
