"""
Unit tests for conversation thread management.

Tests the FIFO logic, thread trimming, and reset functionality.
"""

import pytest

from db import SessionLocal, init_db
from thread_manager import (
    add_message_to_thread,
    get_conversation_thread,
    reset_thread,
    get_thread_summary,
    MAX_THREAD_LENGTH,
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
    """Clean up test users before each test"""
    test_users = ["test_user_basic", "test_user_fifo", "test_user_reset", "test_user_format"]
    for user_id in test_users:
        reset_thread(db_session, user_id)
    yield


@pytest.mark.unit
def test_basic_thread_operations(db_session):
    """Test basic thread operations"""
    test_user_id = "test_user_basic"
    
    # Add first user message
    msg1 = add_message_to_thread(db_session, test_user_id, "user", "What is my sun sign?")
    assert msg1.is_first_pair is True, "First user message should be marked as first_pair"
    
    # Add first assistant message
    msg2 = add_message_to_thread(db_session, test_user_id, "assistant", "Your sun sign is Taurus.")
    assert msg2.is_first_pair is True, "First assistant message should be marked as first_pair"
    
    # Add third message (should not be part of first pair)
    msg3 = add_message_to_thread(db_session, test_user_id, "user", "Tell me more about it")
    assert msg3.is_first_pair is False, "Third message should not be marked as first_pair"
    
    # Check thread
    thread = get_conversation_thread(db_session, test_user_id)
    assert len(thread) == 3, f"Expected 3 messages, got {len(thread)}"
    
    # Check thread summary
    summary = get_thread_summary(db_session, test_user_id)
    assert summary['total_messages'] == 3
    assert summary['fixed_messages'] == 2
    assert summary['user_messages'] == 2
    assert summary['assistant_messages'] == 1


@pytest.mark.unit
def test_fifo_trimming(db_session):
    """Test FIFO trimming when thread exceeds max length"""
    test_user_id = "test_user_fifo"
    
    # Add 12 messages (exceeding MAX_THREAD_LENGTH of 10)
    for i in range(12):
        role = "user" if i % 2 == 0 else "assistant"
        content = f"Message {i + 1}"
        add_message_to_thread(db_session, test_user_id, role, content)
    
    # Check final thread length
    thread = get_conversation_thread(db_session, test_user_id)
    assert len(thread) == MAX_THREAD_LENGTH, f"Expected {MAX_THREAD_LENGTH} messages, got {len(thread)}"
    
    # Verify first pair is still there
    summary = get_thread_summary(db_session, test_user_id)
    assert summary['fixed_messages'] == 2, f"Expected 2 fixed messages, got {summary['fixed_messages']}"
    
    # Verify first two messages are the original first pair
    assert thread[0]['content'] == "Message 1", "First message should be Message 1"
    assert thread[1]['content'] == "Message 2", "Second message should be Message 2"
    
    # Check that oldest non-fixed messages were deleted (Message 3 and 4)
    contents = [msg['content'] for msg in thread]
    assert "Message 3" not in contents, "Message 3 should have been deleted"
    assert "Message 4" not in contents, "Message 4 should have been deleted"
    
    # Latest messages should still be there
    assert "Message 11" in contents, "Message 11 should be in thread"
    assert "Message 12" in contents, "Message 12 should be in thread"


@pytest.mark.unit
def test_reset_thread(db_session):
    """Test thread reset functionality"""
    test_user_id = "test_user_reset"
    
    # Add some messages
    for i in range(5):
        role = "user" if i % 2 == 0 else "assistant"
        add_message_to_thread(db_session, test_user_id, role, f"Message {i + 1}")
    
    thread = get_conversation_thread(db_session, test_user_id)
    assert len(thread) == 5
    
    # Reset thread
    deleted_count = reset_thread(db_session, test_user_id)
    assert deleted_count == 5, f"Expected to delete 5 messages, got {deleted_count}"
    
    # Verify thread is empty
    thread = get_conversation_thread(db_session, test_user_id)
    assert len(thread) == 0, f"Expected empty thread, got {len(thread)} messages"


@pytest.mark.unit
def test_conversation_history_format(db_session):
    """Test that conversation history is in correct format for LLM"""
    test_user_id = "test_user_format"
    
    # Add some messages
    add_message_to_thread(db_session, test_user_id, "user", "Hello!")
    add_message_to_thread(db_session, test_user_id, "assistant", "Hi! How can I help?")
    add_message_to_thread(db_session, test_user_id, "user", "What's my moon sign?")
    
    # Get thread
    thread = get_conversation_thread(db_session, test_user_id)
    assert len(thread) == 3
    
    # Verify format
    for i, msg in enumerate(thread):
        assert 'role' in msg, f"Message {i} missing 'role' key"
        assert 'content' in msg, f"Message {i} missing 'content' key"
        assert msg['role'] in ['user', 'assistant'], f"Invalid role: {msg['role']}"


@pytest.mark.unit
def test_thread_summary_with_empty_thread(db_session):
    """Test thread summary with no messages"""
    test_user_id = "test_user_empty"
    reset_thread(db_session, test_user_id)
    
    summary = get_thread_summary(db_session, test_user_id)
    assert summary['total_messages'] == 0
    assert summary['fixed_messages'] == 0
    assert summary['user_messages'] == 0
    assert summary['assistant_messages'] == 0
    assert summary['oldest_message'] is None
    assert summary['newest_message'] is None


@pytest.mark.unit
def test_multiple_users_isolation(db_session):
    """Test that threads are isolated per user"""
    user1 = "test_user_isolation_1"
    user2 = "test_user_isolation_2"
    
    reset_thread(db_session, user1)
    reset_thread(db_session, user2)
    
    # Add messages for user 1
    add_message_to_thread(db_session, user1, "user", "User 1 message")
    add_message_to_thread(db_session, user1, "assistant", "Response to user 1")
    
    # Add messages for user 2
    add_message_to_thread(db_session, user2, "user", "User 2 message")
    
    # Verify threads are separate
    thread1 = get_conversation_thread(db_session, user1)
    thread2 = get_conversation_thread(db_session, user2)
    
    assert len(thread1) == 2, "User 1 should have 2 messages"
    assert len(thread2) == 1, "User 2 should have 1 message"
    assert thread1[0]['content'] == "User 1 message"
    assert thread2[0]['content'] == "User 2 message"
