"""
Unit tests for message_cache.py

Tests the runtime cache for deduplicating Telegram webhook messages.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.message_cache import (
    is_message_processed,
    mark_message_processed,
    get_cache_stats,
    clear_cache,
    _processed_messages,
    CACHE_EXPIRY_HOURS
)


@pytest.fixture
def clean_cache():
    """Fixture to ensure cache is clean before and after each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.mark.unit
class TestMessageCache:
    """Tests for message deduplication cache."""
    
    def test_message_not_processed_initially(self, clean_cache):
        """Test that a new message is not marked as processed."""
        result = is_message_processed("123456", 1)
        assert result is False
    
    def test_mark_and_check_message_processed(self, clean_cache):
        """Test marking a message as processed and checking it."""
        telegram_id = "123456"
        message_id = 1
        
        # Initially not processed
        assert is_message_processed(telegram_id, message_id) is False
        
        # Mark as processed
        mark_message_processed(telegram_id, message_id)
        
        # Now should be processed
        assert is_message_processed(telegram_id, message_id) is True
    
    def test_different_messages_independent(self, clean_cache):
        """Test that different messages are tracked independently."""
        # Mark first message as processed
        mark_message_processed("123456", 1)
        
        # Different message ID should not be processed
        assert is_message_processed("123456", 2) is False
        
        # Different user ID should not be processed
        assert is_message_processed("789012", 1) is False
        
        # Original message should still be processed
        assert is_message_processed("123456", 1) is True
    
    def test_multiple_messages_from_same_user(self, clean_cache):
        """Test tracking multiple messages from the same user."""
        telegram_id = "123456"
        
        mark_message_processed(telegram_id, 1)
        mark_message_processed(telegram_id, 2)
        mark_message_processed(telegram_id, 3)
        
        assert is_message_processed(telegram_id, 1) is True
        assert is_message_processed(telegram_id, 2) is True
        assert is_message_processed(telegram_id, 3) is True
        assert is_message_processed(telegram_id, 4) is False
    
    def test_cache_stats(self, clean_cache):
        """Test cache statistics reporting."""
        # Initially empty
        stats = get_cache_stats()
        assert stats["total_entries"] == 0
        assert stats["cache_expiry_hours"] == CACHE_EXPIRY_HOURS
        
        # Add some entries
        mark_message_processed("user1", 1)
        mark_message_processed("user2", 2)
        mark_message_processed("user3", 3)
        
        stats = get_cache_stats()
        assert stats["total_entries"] == 3
    
    def test_clear_cache(self, clean_cache):
        """Test clearing the cache."""
        # Add entries
        mark_message_processed("user1", 1)
        mark_message_processed("user2", 2)
        
        assert get_cache_stats()["total_entries"] == 2
        
        # Clear cache
        clear_cache()
        
        assert get_cache_stats()["total_entries"] == 0
        assert is_message_processed("user1", 1) is False
    
    def test_cache_cleanup_removes_old_entries(self, clean_cache):
        """Test that old entries are cleaned up automatically."""
        # Add an entry with timestamp in the past
        telegram_id = "123456"
        message_id = 1
        old_timestamp = datetime.now(timezone.utc) - timedelta(hours=CACHE_EXPIRY_HOURS + 1)
        
        # Directly manipulate cache to add old entry
        _processed_messages[(telegram_id, message_id)] = old_timestamp
        
        # Add a new entry (this triggers cleanup)
        mark_message_processed("789012", 2)
        
        # Old entry should be cleaned up
        assert (telegram_id, message_id) not in _processed_messages
        # New entry should still be there
        assert ("789012", 2) in _processed_messages
    
    def test_cache_cleanup_keeps_recent_entries(self, clean_cache):
        """Test that recent entries are not cleaned up."""
        # Add recent entries
        mark_message_processed("user1", 1)
        mark_message_processed("user2", 2)
        
        # Add another entry (triggers cleanup)
        mark_message_processed("user3", 3)
        
        # All recent entries should still be there
        assert is_message_processed("user1", 1) is True
        assert is_message_processed("user2", 2) is True
        assert is_message_processed("user3", 3) is True
    
    def test_duplicate_message_ids_different_users(self, clean_cache):
        """Test that same message ID from different users are tracked separately."""
        # Same message ID from different users
        mark_message_processed("user1", 100)
        mark_message_processed("user2", 100)
        
        # Both should be marked as processed
        assert is_message_processed("user1", 100) is True
        assert is_message_processed("user2", 100) is True
        
        # Different user with same message ID should not be processed
        assert is_message_processed("user3", 100) is False
    
    def test_string_telegram_id_handling(self, clean_cache):
        """Test that string telegram IDs are handled correctly."""
        # Test with string IDs (as they come from Telegram API)
        mark_message_processed("123456789", 1)
        
        assert is_message_processed("123456789", 1) is True
        assert is_message_processed("987654321", 1) is False
