"""
Unit tests for user profile management.

Tests the LLM-maintained user profile functionality:
- Profile creation and retrieval
- Profile updates
- Profile length limits
- Old data preservation
- Integration with conversation flow
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.db import SessionLocal, init_db
from src.models import User
from src.user_profile_manager import (
    UserProfileManager,
    update_profile_after_interaction,
    MAX_PROFILE_LENGTH
)


@pytest.fixture(scope="module")
def db_session():
    """Create database session for tests"""
    init_db()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def cleanup_test_users(db_session):
    """Clean up test users before and after each test"""
    test_users = [
        "test_profile_user",
        "test_profile_update",
        "test_profile_length",
        "test_profile_preserve",
        "test_profile_none"
    ]
    for user_id in test_users:
        user = db_session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            db_session.delete(user)
    db_session.commit()
    yield
    # Cleanup after test
    for user_id in test_users:
        user = db_session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            db_session.delete(user)
    db_session.commit()


@pytest.mark.unit
class TestUserProfileManager:
    """Tests for UserProfileManager class."""

    def test_get_user_profile_none_when_no_user(self, db_session):
        """Test getting profile for non-existent user returns None."""
        profile = UserProfileManager.get_user_profile(db_session, "nonexistent_user")
        assert profile is None, "Should return None for non-existent user"

    def test_get_user_profile_none_when_no_profile(self, db_session):
        """Test getting profile when user exists but has no profile."""
        # Create user without profile
        user = User(telegram_id="test_profile_none")
        db_session.add(user)
        db_session.commit()
        
        profile = UserProfileManager.get_user_profile(db_session, "test_profile_none")
        assert profile is None, "Should return None when user has no profile"

    def test_update_and_get_user_profile(self, db_session):
        """Test updating and retrieving user profile."""
        # Create user
        user = User(telegram_id="test_profile_user")
        db_session.add(user)
        db_session.commit()
        
        # Update profile
        test_profile = "Пользователь предпочитает краткие ответы."
        UserProfileManager.update_user_profile(db_session, "test_profile_user", test_profile)
        
        # Retrieve profile
        retrieved = UserProfileManager.get_user_profile(db_session, "test_profile_user")
        assert retrieved == test_profile, "Retrieved profile should match saved profile"

    def test_update_profile_truncates_if_too_long(self, db_session):
        """Test that profile is truncated if exceeds MAX_PROFILE_LENGTH."""
        # Create user
        user = User(telegram_id="test_profile_length")
        db_session.add(user)
        db_session.commit()
        
        # Create profile that exceeds limit
        long_profile = "А" * (MAX_PROFILE_LENGTH + 1000)
        UserProfileManager.update_user_profile(db_session, "test_profile_length", long_profile)
        
        # Retrieve and verify truncation
        retrieved = UserProfileManager.get_user_profile(db_session, "test_profile_length")
        assert len(retrieved) == MAX_PROFILE_LENGTH, f"Profile should be truncated to {MAX_PROFILE_LENGTH} chars"

    def test_update_profile_preserves_existing_user_data(self, db_session):
        """Test that updating profile doesn't affect other user data."""
        # Create user with existing data
        user = User(
            telegram_id="test_profile_preserve",
            state="chatting_about_chart",
            missing_fields="dob,time",
            assistant_mode=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Update profile
        test_profile = "Новый профиль пользователя."
        UserProfileManager.update_user_profile(db_session, "test_profile_preserve", test_profile)
        
        # Verify other data is preserved
        updated_user = db_session.query(User).filter_by(telegram_id="test_profile_preserve").first()
        assert updated_user.state == "chatting_about_chart", "User state should be preserved"
        assert updated_user.missing_fields == "dob,time", "Missing fields should be preserved"
        assert updated_user.assistant_mode is True, "Assistant mode should be preserved"
        assert updated_user.user_profile == test_profile, "Profile should be updated"

    def test_update_profile_multiple_times(self, db_session):
        """Test updating profile multiple times (profile evolution)."""
        # Create user
        user = User(telegram_id="test_profile_update")
        db_session.add(user)
        db_session.commit()
        
        # First update
        profile1 = "Первое взаимодействие: пользователь задал вопрос о карьере."
        UserProfileManager.update_user_profile(db_session, "test_profile_update", profile1)
        retrieved1 = UserProfileManager.get_user_profile(db_session, "test_profile_update")
        assert retrieved1 == profile1
        
        # Second update
        profile2 = "Второе взаимодействие: интересуется карьерой и отношениями."
        UserProfileManager.update_user_profile(db_session, "test_profile_update", profile2)
        retrieved2 = UserProfileManager.get_user_profile(db_session, "test_profile_update")
        assert retrieved2 == profile2, "Profile should be updated to new value"
        
        # Third update
        profile3 = "Третье взаимодействие: предпочитает детальные ответы о карьере и финансах."
        UserProfileManager.update_user_profile(db_session, "test_profile_update", profile3)
        retrieved3 = UserProfileManager.get_user_profile(db_session, "test_profile_update")
        assert retrieved3 == profile3, "Profile should be updated to latest value"

    def test_build_profile_prompt_with_no_current_profile(self, db_session):
        """Test building prompt when user has no existing profile."""
        prompt = UserProfileManager.build_profile_prompt(
            current_profile=None,
            conversation_history=[],
            latest_user_message="Как у меня с карьерой?",
            latest_assistant_response="В вашей карте показано..."
        )
        
        assert "CURRENT PROFILE: None" in prompt, "Should indicate no existing profile"
        assert "Как у меня с карьерой?" in prompt, "Should include latest user message"
        assert "В вашей карте показано" in prompt, "Should include latest response"

    def test_build_profile_prompt_with_existing_profile(self, db_session):
        """Test building prompt when user has existing profile."""
        existing_profile = "Пользователь интересуется карьерой."
        prompt = UserProfileManager.build_profile_prompt(
            current_profile=existing_profile,
            conversation_history=[
                {"role": "user", "content": "Первый вопрос"},
                {"role": "assistant", "content": "Первый ответ"},
                {"role": "user", "content": "Еще вопрос"}
            ],
            latest_user_message="Второй вопрос",
            latest_assistant_response="Второй ответ"
        )
        
        assert existing_profile in prompt, "Should include existing profile"
        assert "Второй вопрос" in prompt, "Should include latest user message"
        assert "Второй ответ" in prompt, "Should include latest response"
        # Conversation history is included when length > 2
        assert "Первый вопрос" in prompt, "Should include conversation history"

    def test_build_profile_prompt_truncates_long_response(self, db_session):
        """Test that long assistant responses are truncated in prompt."""
        long_response = "А" * 1000
        prompt = UserProfileManager.build_profile_prompt(
            current_profile=None,
            conversation_history=[],
            latest_user_message="Вопрос",
            latest_assistant_response=long_response
        )
        
        # Response should be truncated to 500 chars + "..."
        assert "А" * 500 in prompt, "Should include first 500 chars"
        assert "..." in prompt, "Should have ellipsis for truncation"
        assert len([line for line in prompt.split('\n') if "А" * 600 in line]) == 0, "Should not include full 1000 chars"


@pytest.mark.unit
class TestProfileUpdateIntegration:
    """Tests for profile update integration with LLM."""

    def test_update_profile_after_interaction_success(self, db_session):
        """Test successful profile update after interaction."""
        # Setup
        user = User(telegram_id="test_integration_user")
        db_session.add(user)
        db_session.commit()
        
        # Create a mock call_llm function
        mock_call_llm = Mock(return_value="Обновленный профиль пользователя.")
        
        # Call update with mocked call_llm
        update_profile_after_interaction(
            session=db_session,
            telegram_id="test_integration_user",
            conversation_history=[
                {"role": "user", "content": "Привет"},
                {"role": "assistant", "content": "Привет!"}
            ],
            latest_user_message="Как дела?",
            latest_assistant_response="Хорошо!",
            call_llm_func=mock_call_llm
        )
        
        # Verify LLM was called
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args
        assert call_args.kwargs['prompt_type'] == "parser/update_user_profile"
        assert call_args.kwargs['temperature'] == 0.3
        assert call_args.kwargs['is_parser'] is True
        
        # Verify profile was saved
        profile = UserProfileManager.get_user_profile(db_session, "test_integration_user")
        assert profile == "Обновленный профиль пользователя."
        
        # Cleanup
        db_session.query(User).filter_by(telegram_id="test_integration_user").delete()
        db_session.commit()

    def test_update_profile_after_interaction_llm_error(self, db_session):
        """Test that LLM errors don't break the flow."""
        # Setup
        user = User(telegram_id="test_integration_error")
        db_session.add(user)
        db_session.commit()
        
        # Create a mock that raises an error
        mock_call_llm = Mock(side_effect=Exception("LLM API error"))
        
        # Call update - should not raise exception
        try:
            update_profile_after_interaction(
                session=db_session,
                telegram_id="test_integration_error",
                conversation_history=[],
                latest_user_message="Test",
                latest_assistant_response="Response",
                call_llm_func=mock_call_llm
            )
        except Exception:
            pytest.fail("update_profile_after_interaction should not raise exception on LLM error")
        
        # Profile should not be created due to error
        profile = UserProfileManager.get_user_profile(db_session, "test_integration_error")
        assert profile is None, "Profile should not be created when LLM fails"
        
        # Cleanup
        db_session.query(User).filter_by(telegram_id="test_integration_error").delete()
        db_session.commit()

    def test_update_profile_preserves_existing_data_on_update(self, db_session):
        """Test that profile updates preserve all other user data."""
        # Setup user with existing data
        user = User(
            telegram_id="test_preserve_data",
            state="chatting_about_chart",
            natal_chart_json='{"sun": "Aries"}',
            missing_fields=None,
            assistant_mode=True,
            user_profile="Старый профиль"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a mock call_llm function
        mock_call_llm = Mock(return_value="Новый профиль")
        
        # Update profile
        update_profile_after_interaction(
            session=db_session,
            telegram_id="test_preserve_data",
            conversation_history=[],
            latest_user_message="Тест",
            latest_assistant_response="Ответ",
            call_llm_func=mock_call_llm
        )
        
        # Verify all data preserved
        updated_user = db_session.query(User).filter_by(telegram_id="test_preserve_data").first()
        assert updated_user.state == "chatting_about_chart", "State should be preserved"
        assert updated_user.natal_chart_json == '{"sun": "Aries"}', "Natal chart should be preserved"
        assert updated_user.missing_fields is None, "Missing fields should be preserved"
        assert updated_user.assistant_mode is True, "Assistant mode should be preserved"
        assert updated_user.user_profile == "Новый профиль", "Profile should be updated"
        
        # Cleanup
        db_session.query(User).filter_by(telegram_id="test_preserve_data").delete()
        db_session.commit()


@pytest.mark.unit
class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing data."""

    def test_existing_users_without_profile_work(self, db_session):
        """Test that existing users without profile column still work."""
        # Simulate existing user (no profile)
        user = User(
            telegram_id="test_legacy_user",
            state="has_chart",
            natal_chart_json='{"planets": []}'
        )
        db_session.add(user)
        db_session.commit()
        
        # Should return None for profile
        profile = UserProfileManager.get_user_profile(db_session, "test_legacy_user")
        assert profile is None, "Legacy users should have None profile"
        
        # Should be able to update profile
        UserProfileManager.update_user_profile(db_session, "test_legacy_user", "Новый профиль")
        
        # Verify update worked and other data preserved
        updated_user = db_session.query(User).filter_by(telegram_id="test_legacy_user").first()
        assert updated_user.user_profile == "Новый профиль"
        assert updated_user.state == "has_chart", "State should be preserved"
        assert updated_user.natal_chart_json == '{"planets": []}', "Chart should be preserved"
        
        # Cleanup
        db_session.query(User).filter_by(telegram_id="test_legacy_user").delete()
        db_session.commit()

    def test_profile_column_is_nullable(self, db_session):
        """Test that user_profile column is nullable (doesn't break existing data)."""
        # Create user without specifying profile
        user = User(telegram_id="test_nullable")
        db_session.add(user)
        db_session.commit()
        
        # Verify user was created successfully
        created_user = db_session.query(User).filter_by(telegram_id="test_nullable").first()
        assert created_user is not None, "User should be created without profile"
        assert created_user.user_profile is None, "Profile should be None by default"
        
        # Cleanup
        db_session.query(User).filter_by(telegram_id="test_nullable").delete()
        db_session.commit()
