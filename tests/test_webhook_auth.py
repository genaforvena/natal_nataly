import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

@pytest.fixture
def client():
    # Force reload of src.main if needed, or just import
    # But usually TestClient(app) is enough if we mock os.getenv inside the route
    from src.main import app
    return TestClient(app)

@pytest.fixture
def mock_update():
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 987654321},
            "chat": {"id": 987654321},
            "text": "hello"
        }
    }

@patch('src.main.handle_telegram_update')
@patch('src.main.init_db')  # Mock init_db to avoid DB issues
def test_webhook_no_token_required(mock_init_db, mock_handle, client, mock_update):
    """Test webhook when no secret token is configured in environment."""
    with patch('os.getenv', side_effect=lambda k, d=None: None if k == "TELEGRAM_SECRET_TOKEN" else os.environ.get(k, d)):
        mock_handle.return_value = {"ok": True}
        response = client.post("/webhook", json=mock_update)
        assert response.status_code == 200
        assert response.json() == {"ok": True}

@patch('src.main.handle_telegram_update')
@patch('src.main.init_db')
def test_webhook_with_valid_token(mock_init_db, mock_handle, client, mock_update):
    """Test webhook with valid secret token."""
    secret = "my_secret_token"
    with patch('os.getenv', side_effect=lambda k, d=None: secret if k == "TELEGRAM_SECRET_TOKEN" else os.environ.get(k, d)):
        mock_handle.return_value = {"ok": True}
        headers = {"X-Telegram-Bot-Api-Secret-Token": secret}
        response = client.post("/webhook", json=mock_update, headers=headers)
        assert response.status_code == 200
        assert response.json() == {"ok": True}

@patch('src.main.handle_telegram_update')
@patch('src.main.init_db')
def test_webhook_with_invalid_token(mock_init_db, mock_handle, client, mock_update):
    """Test webhook with invalid secret token."""
    secret = "my_secret_token"
    with patch('os.getenv', side_effect=lambda k, d=None: secret if k == "TELEGRAM_SECRET_TOKEN" else os.environ.get(k, d)):
        headers = {"X-Telegram-Bot-Api-Secret-Token": "wrong_token"}
        response = client.post("/webhook", json=mock_update, headers=headers)
        assert response.status_code == 403
        assert response.json() == {"detail": "Unauthorized"}

@patch('src.main.handle_telegram_update')
@patch('src.main.init_db')
def test_webhook_missing_token_when_required(mock_init_db, mock_handle, client, mock_update):
    """Test webhook missing secret token when one is configured."""
    secret = "my_secret_token"
    with patch('os.getenv', side_effect=lambda k, d=None: secret if k == "TELEGRAM_SECRET_TOKEN" else os.environ.get(k, d)):
        response = client.post("/webhook", json=mock_update)
        assert response.status_code == 403
        assert response.json() == {"detail": "Unauthorized"}
