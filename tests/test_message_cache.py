"""
Unit tests for message_cache.py

Tests the runtime cache for deduplicating Telegram webhook messages.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.db import init_db
from src.message_cache import (
    mark_if_new,
    get_cache_stats,
    clear_cache,
    CACHE_EXPIRY_HOURS
)
# Import _processed_messages only for testing expiry behavior
from src.message_cache import _processed_messages, _cache_lock


@pytest.fixture(scope="module", autouse=True)
def initialize_database():
    """Initialize database before running tests."""
    init_db()
    yield


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
        result = mark_if_new("123456", 1)
        assert result is True  # Message was new
    
    def test_mark_and_check_message_processed(self, clean_cache):
        """Test marking a message as processed and checking it."""
        telegram_id = "123456"
        message_id = 1
        
        # First call - message is new
        assert mark_if_new(telegram_id, message_id) is True
        
        # Second call - message is duplicate
        assert mark_if_new(telegram_id, message_id) is False
    
    def test_different_messages_independent(self, clean_cache):
        """Test that different messages are tracked independently."""
        # Mark first message as processed
        mark_if_new("123456", 1)
        
        # Different message ID should not be processed
        assert mark_if_new("123456", 2) is True
        
        # Different user ID should not be processed
        assert mark_if_new("789012", 1) is True
        
        # Original message should be duplicate
        assert mark_if_new("123456", 1) is False
    
    def test_multiple_messages_from_same_user(self, clean_cache):
        """Test tracking multiple messages from the same user."""
        telegram_id = "123456"
        
        assert mark_if_new(telegram_id, 1) is True
        assert mark_if_new(telegram_id, 2) is True
        assert mark_if_new(telegram_id, 3) is True
        
        # All should now be duplicates
        assert mark_if_new(telegram_id, 1) is False
        assert mark_if_new(telegram_id, 2) is False
        assert mark_if_new(telegram_id, 3) is False
        
        # New message should be accepted
        assert mark_if_new(telegram_id, 4) is True
    
    def test_cache_stats(self, clean_cache):
        """Test cache statistics reporting."""
        # Initially empty
        stats = get_cache_stats()
        assert stats["memory_entries"] == 0
        assert stats["cache_expiry_hours"] == CACHE_EXPIRY_HOURS
        assert "db_entries" in stats
        
        # Add some entries
        mark_if_new("user1", 1)
        mark_if_new("user2", 2)
        mark_if_new("user3", 3)
        
        stats = get_cache_stats()
        assert stats["memory_entries"] == 3
        assert stats["db_entries"] >= 3  # Database should have at least these entries
    
    def test_clear_cache(self, clean_cache):
        """Test clearing the cache."""
        # Add entries
        mark_if_new("user1", 1)
        mark_if_new("user2", 2)
        
        assert get_cache_stats()["memory_entries"] >= 2
        
        # Clear cache
        clear_cache()
        
        assert get_cache_stats()["memory_entries"] == 0
        assert get_cache_stats()["db_entries"] == 0
        assert mark_if_new("user1", 1) is True  # Should be new again
    
    def test_cache_cleanup_removes_old_entries(self, clean_cache):
        """Test that old entries are cleaned up automatically."""
        # Add an entry with timestamp in the past
        telegram_id = "123456"
        message_id = 1
        old_timestamp = datetime.now(timezone.utc) - timedelta(hours=CACHE_EXPIRY_HOURS + 1)
        
        # Directly manipulate cache to add old entry (use lock for thread safety)
        with _cache_lock:
            _processed_messages[(telegram_id, message_id)] = old_timestamp
        
        # Add a new entry (this triggers cleanup)
        mark_if_new("789012", 2)
        
        # Old entry should be cleaned up
        with _cache_lock:
            assert (telegram_id, message_id) not in _processed_messages
            # New entry should still be there
            assert ("789012", 2) in _processed_messages
    
    def test_expired_entry_treated_as_new(self, clean_cache):
        """Test that expired entries are treated as new messages."""
        telegram_id = "123456"
        message_id = 1
        old_timestamp = datetime.now(timezone.utc) - timedelta(hours=CACHE_EXPIRY_HOURS + 1)
        
        # Directly add an expired entry
        with _cache_lock:
            _processed_messages[(telegram_id, message_id)] = old_timestamp
        
        # Should be treated as new (expired)
        assert mark_if_new(telegram_id, message_id) is True
    
    def test_cache_cleanup_keeps_recent_entries(self, clean_cache):
        """Test that recent entries are not cleaned up."""
        # Add recent entries
        mark_if_new("user1", 1)
        mark_if_new("user2", 2)
        
        # Add another entry (triggers cleanup)
        mark_if_new("user3", 3)
        
        # All recent entries should still be there (duplicates)
        assert mark_if_new("user1", 1) is False
        assert mark_if_new("user2", 2) is False
        assert mark_if_new("user3", 3) is False
    
    def test_duplicate_message_ids_different_users(self, clean_cache):
        """Test that same message ID from different users are tracked separately."""
        # Same message ID from different users
        mark_if_new("user1", 100)
        mark_if_new("user2", 100)
        
        # Both should be marked as processed (duplicates now)
        assert mark_if_new("user1", 100) is False
        assert mark_if_new("user2", 100) is False
        
        # Different user with same message ID should be new
        assert mark_if_new("user3", 100) is True
    
    def test_string_telegram_id_handling(self, clean_cache):
        """Test that string telegram IDs are handled correctly."""
        # Test with string IDs (as they come from Telegram API)
        assert mark_if_new("123456789", 1) is True
        
        assert mark_if_new("123456789", 1) is False  # Duplicate
        assert mark_if_new("987654321", 1) is True  # Different user
    
    def test_concurrent_access_safety(self, clean_cache):
        """Test that cache operations are thread-safe."""
        import threading
        
        results = []
        
        def mark_message():
            result = mark_if_new("user1", 1)
            results.append(result)
        
        # Create multiple threads trying to mark the same message
        threads = [threading.Thread(target=mark_message) for _ in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Exactly one thread should have successfully marked it as new
        assert sum(results) == 1
    
    def test_persistence_across_restart_simulation(self, clean_cache):
        """Test that messages persist across simulated restart (in-memory cache cleared)."""
        # Mark a message as processed
        telegram_id = "test_user"
        message_id = 999
        
        # First time should be new
        assert mark_if_new(telegram_id, message_id) is True
        
        # Second time should be duplicate (in-memory hit)
        assert mark_if_new(telegram_id, message_id) is False
        
        # Simulate restart by clearing in-memory cache only
        with _cache_lock:
            _processed_messages.clear()
        
        # After "restart", message should still be detected as duplicate (database hit)
        assert mark_if_new(telegram_id, message_id) is False
        
        # Verify message is back in memory cache after database hit
        with _cache_lock:
            assert (telegram_id, message_id) in _processed_messages
