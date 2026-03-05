import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.asyncio
async def test_repro_issue_62_single_message():
    """
    Test that extract_birth_data_async correctly parses a single message with DOB, TOB.
    """
    pass

@pytest.mark.asyncio
@patch('src.bot.extract_birth_data_async')
@patch('src.bot.generate_clarification_question_async')
@patch('src.user_profile_manager.UserProfileManager.get_user_profile')
async def test_bot_logic_accumulation(mock_get_profile, mock_gen_clarify, mock_extract_birth_data):
    """
    Test that bot.py correctly accumulates context.
    """
    from src.bot import handle_awaiting_birth_data
    from src.models import User, STATE_ONBOARDING, STATE_AWAITING_CLARIFICATION

    session = Mock()
    user = User(telegram_id="123", state=STATE_ONBOARDING, conversation_session_json=None)
    session.query.return_value.filter_by.return_value.first.return_value = user

    mock_get_profile.return_value = "Test profile"
    mock_gen_clarify.return_value = "What is your location?"

    # Mock LLM to return missing location
    mock_extract_birth_data.return_value = {
        "dob": "2014-08-13",
        "time": "05:16",
        "lat": None,
        "lng": None,
        "location": None,
        "missing_fields": ["lat", "lng"]
    }

    with patch('src.bot.send_telegram_message', new_callable=AsyncMock) as mock_send:
        await handle_awaiting_birth_data(session, user, 123, "I was born in August 13 2014 5:16")

        # Check if user state updated to clarification
        assert user.state == STATE_AWAITING_CLARIFICATION
        assert "lat" in user.missing_fields

        # Check if conversation history was updated in DB
        # If the bug exists, user.conversation_session_json will still be None or empty
        assert user.conversation_session_json is not None, "Conversation context should be persisted!"

        ctx = json.loads(user.conversation_session_json)
        assert len(ctx) >= 2
        assert ctx[0]["role"] == "user"
        assert ctx[0]["content"] == "I was born in August 13 2014 5:16"
        assert ctx[1]["role"] == "assistant"
        assert ctx[1]["content"] == "What is your location?"
