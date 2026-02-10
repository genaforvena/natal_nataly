"""
Thread Manager - Conversation Thread Management

Manages conversation threads for users with the following rules:
- Max 10 messages per user thread
- First 2 messages (user + assistant) are never deleted (fixed pair)
- Remaining messages follow FIFO (First In First Out) deletion
- When thread exceeds 10 messages, oldest non-fixed messages are deleted
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import ConversationMessage

logger = logging.getLogger(__name__)

# Constants
MAX_THREAD_LENGTH = 10
FIXED_PAIR_COUNT = 2  # First user message + first assistant response


def add_message_to_thread(session: Session, telegram_id: str, role: str, content: str) -> ConversationMessage:
    """
    Add a message to the user's conversation thread.
    Automatically marks first pair and trims thread if needed.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        role: "user" or "assistant"
        content: Message text or summary
        
    Returns:
        Created ConversationMessage object
    """
    logger.debug(f"Adding message to thread: telegram_id={telegram_id}, role={role}, content_length={len(content)}")
    
    try:
        # Check if this is part of the first pair
        existing_messages = session.query(ConversationMessage)\
            .filter_by(telegram_id=telegram_id)\
            .order_by(ConversationMessage.created_at)\
            .all()
        
        # Determine if this message is part of the first pair
        is_first_pair = False
        if len(existing_messages) == 0 and role == "user":
            # First user message
            is_first_pair = True
        elif len(existing_messages) == 1 and existing_messages[0].role == "user" and role == "assistant":
            # First assistant response (after first user message)
            is_first_pair = True
        
        # Create new message
        new_message = ConversationMessage(
            telegram_id=telegram_id,
            role=role,
            content=content,
            is_first_pair=is_first_pair,
            created_at=datetime.now(timezone.utc)
        )
        
        session.add(new_message)
        session.commit()
        
        logger.info(f"Message added to thread: id={new_message.id}, is_first_pair={is_first_pair}")
        
        # Trim thread if needed
        trim_thread_if_needed(session, telegram_id)
        
        return new_message
        
    except Exception as e:
        logger.exception(f"Error adding message to thread for {telegram_id}: {e}")
        session.rollback()
        raise


def get_conversation_thread(session: Session, telegram_id: str) -> List[Dict[str, str]]:
    """
    Retrieve the current conversation thread for a user.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        
    Returns:
        List of message dictionaries with 'role' and 'content' keys,
        ordered chronologically (oldest first)
    """
    logger.debug(f"Retrieving conversation thread for telegram_id={telegram_id}")
    
    try:
        messages = session.query(ConversationMessage)\
            .filter_by(telegram_id=telegram_id)\
            .order_by(ConversationMessage.created_at)\
            .all()
        
        thread = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]
        
        logger.info(f"Retrieved {len(thread)} messages from thread for {telegram_id}")
        
        return thread
        
    except Exception as e:
        logger.exception(f"Error retrieving conversation thread for {telegram_id}: {e}")
        raise


def trim_thread_if_needed(session: Session, telegram_id: str):
    """
    Trim thread to MAX_THREAD_LENGTH if exceeded.
    Keeps first pair fixed, removes oldest non-fixed messages (FIFO).
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
    """
    logger.debug(f"Checking if thread needs trimming for telegram_id={telegram_id}")
    
    try:
        # Get all messages ordered by creation time
        messages = session.query(ConversationMessage)\
            .filter_by(telegram_id=telegram_id)\
            .order_by(ConversationMessage.created_at)\
            .all()
        
        message_count = len(messages)
        
        if message_count <= MAX_THREAD_LENGTH:
            logger.debug(f"Thread size OK: {message_count}/{MAX_THREAD_LENGTH}")
            return
        
        # Calculate how many messages to delete
        messages_to_delete = message_count - MAX_THREAD_LENGTH
        
        logger.info(f"Thread exceeds limit: {message_count}/{MAX_THREAD_LENGTH}. Deleting {messages_to_delete} messages")
        
        # Separate fixed and non-fixed messages
        fixed_messages = [msg for msg in messages if msg.is_first_pair]
        non_fixed_messages = [msg for msg in messages if not msg.is_first_pair]
        
        # Delete oldest non-fixed messages (FIFO)
        for msg in non_fixed_messages[:messages_to_delete]:
            logger.debug(f"Deleting message: id={msg.id}, role={msg.role}, created_at={msg.created_at}")
            session.delete(msg)
        
        session.commit()
        
        logger.info(f"Thread trimmed successfully. Deleted {messages_to_delete} messages")
        
    except Exception as e:
        logger.exception(f"Error trimming thread for {telegram_id}: {e}")
        session.rollback()
        raise


def reset_thread(session: Session, telegram_id: str):
    """
    Reset (clear) the entire conversation thread for a user.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
    """
    logger.info(f"Resetting conversation thread for telegram_id={telegram_id}")
    
    try:
        # Delete all messages for this user
        deleted_count = session.query(ConversationMessage)\
            .filter_by(telegram_id=telegram_id)\
            .delete()
        
        session.commit()
        
        logger.info(f"Thread reset complete. Deleted {deleted_count} messages")
        
        return deleted_count
        
    except Exception as e:
        logger.exception(f"Error resetting thread for {telegram_id}: {e}")
        session.rollback()
        raise


def get_thread_summary(session: Session, telegram_id: str) -> Dict[str, Any]:
    """
    Get summary statistics about the user's thread.
    Useful for debugging and analytics.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        
    Returns:
        Dictionary with thread statistics
    """
    logger.debug(f"Getting thread summary for telegram_id={telegram_id}")
    
    try:
        messages = session.query(ConversationMessage)\
            .filter_by(telegram_id=telegram_id)\
            .order_by(ConversationMessage.created_at)\
            .all()
        
        summary = {
            "total_messages": len(messages),
            "fixed_messages": sum(1 for msg in messages if msg.is_first_pair),
            "user_messages": sum(1 for msg in messages if msg.role == "user"),
            "assistant_messages": sum(1 for msg in messages if msg.role == "assistant"),
            "oldest_message": messages[0].created_at if messages else None,
            "newest_message": messages[-1].created_at if messages else None
        }
        
        logger.debug(f"Thread summary: {summary}")
        
        return summary
        
    except Exception as e:
        logger.exception(f"Error getting thread summary for {telegram_id}: {e}")
        raise
