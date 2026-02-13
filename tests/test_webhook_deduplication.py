"""
Integration test for webhook deduplication in main.py

Tests the webhook endpoint's deduplication logic.
"""

import pytest
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


@pytest.mark.integration
class TestWebhookDeduplication:
    """Integration tests for webhook message deduplication."""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint works."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_webhook_with_duplicate_message_skips_second(self, client):
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
        # Should not have skipped field
        assert "skipped" not in result1 or result1.get("skipped") != "duplicate"
        
        # Second request with same message_id should be skipped
        response2 = client.post("/webhook", json=webhook_data)
        assert response2.status_code == 200
        result2 = response2.json()
        assert result2.get("ok") is True
        assert result2.get("skipped") == "duplicate"
    
    def test_webhook_different_messages_not_skipped(self, client):
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
        assert response1.json().get("skipped") != "duplicate"
        
        response2 = client.post("/webhook", json=webhook_data2)
        assert response2.status_code == 200
        assert response2.json().get("skipped") != "duplicate"
    
    def test_webhook_same_message_id_different_users(self, client):
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
        assert response1.json().get("skipped") != "duplicate"
        
        response2 = client.post("/webhook", json=webhook_data2)
        assert response2.status_code == 200
        assert response2.json().get("skipped") != "duplicate"
    
    def test_webhook_missing_message_id(self, client):
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
    
    def test_webhook_missing_user_id(self, client):
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
