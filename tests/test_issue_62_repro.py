import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

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


@pytest.mark.asyncio
@patch('src.bot.extract_birth_data_async')
@patch('src.bot.generate_clarification_question_async')
@patch('src.user_profile_manager.UserProfileManager.get_user_profile')
async def test_bot_multi_turn_accumulation(mock_get_profile, mock_gen_clarify, mock_extract_birth_data):
    """
    Test that data accumulation works across multiple turns during onboarding.
    Turn 1: "I was born in London" -> missing dob, time
    Turn 2: "on Aug 13 2014" -> missing time
    Turn 3: "at 5:16" -> all data present
    """
    from src.bot import handle_awaiting_birth_data, handle_awaiting_clarification
    from src.models import User, STATE_ONBOARDING, STATE_AWAITING_CLARIFICATION, STATE_AWAITING_CONFIRMATION

    session = Mock()
    user = User(telegram_id="123", state=STATE_ONBOARDING, conversation_session_json=None)
    session.query.return_value.filter_by.return_value.first.return_value = user
    mock_get_profile.return_value = "Test profile"

    # TURN 1: Location provided
    mock_extract_birth_data.return_value = {
        "dob": None, "time": None, "lat": 51.5074, "lng": -0.1278,
        "location": "London", "missing_fields": ["dob", "time"]
    }
    mock_gen_clarify.return_value = "When were you born?"

    with patch('src.bot.send_telegram_message', new_callable=AsyncMock):
        await handle_awaiting_birth_data(session, user, 123, "I was born in London")
        assert user.state == STATE_AWAITING_CLARIFICATION
        assert "dob" in user.missing_fields
        assert session.commit.called, "Session commit should be called after turn 1"

    # TURN 2: DOB provided
    mock_extract_birth_data.return_value = {
        "dob": "2014-08-13", "time": None, "lat": 51.5074, "lng": -0.1278,
        "location": "London", "missing_fields": ["time"]
    }
    mock_gen_clarify.return_value = "At what time?"

    with patch('src.bot.send_telegram_message', new_callable=AsyncMock):
        await handle_awaiting_clarification(session, user, 123, "on Aug 13 2014")
        assert user.state == STATE_AWAITING_CLARIFICATION
        assert user.missing_fields == "time"
        assert session.commit.called, "Session commit should be called after turn 2"

    # TURN 3: Time provided
    mock_extract_birth_data.return_value = {
        "dob": "2014-08-13", "time": "05:16", "lat": 51.5074, "lng": -0.1278,
        "location": "London", "missing_fields": []
    }

    with patch('src.bot.send_telegram_message', new_callable=AsyncMock), \
         patch('src.bot.validate_timezone') as mock_tz:
        mock_tz.return_value = {"timezone": "Europe/London", "source": "test", "validation_status": "OK"}
        await handle_awaiting_clarification(session, user, 123, "at 5:16")

        # After Turn 3, it should move to confirmation (or HAS_CHART if handle_awaiting_clarification skips confirmation)
        # Checking current handle_awaiting_clarification implementation: it directly generates chart and sets HAS_CHART.
        assert user.state == "has_chart"
