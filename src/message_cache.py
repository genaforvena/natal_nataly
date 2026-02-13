"""
Runtime cache for tracking processed Telegram messages.

This module implements a simple in-memory cache to prevent duplicate processing
of the same message when Telegram webhooks are triggered multiple times.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# In-memory cache: (telegram_id, message_id) -> timestamp
# Stores when each message was last processed
_processed_messages: Dict[Tuple[str, int], datetime] = {}

# Cache configuration
CACHE_EXPIRY_HOURS = 24  # How long to keep entries in cache


def is_message_processed(telegram_id: str, message_id: int) -> bool:
    """
    Check if a message has already been processed.
    
    Args:
        telegram_id: Telegram user ID
        message_id: Telegram message ID
        
    Returns:
        True if message was already processed, False otherwise
    """
    key = (telegram_id, message_id)
    
    if key in _processed_messages:
        processed_time = _processed_messages[key]
        logger.info(f"Message {message_id} from user {telegram_id} was already processed at {processed_time}")
        return True
    
    return False


def mark_message_processed(telegram_id: str, message_id: int) -> None:
    """
    Mark a message as processed in the cache.
    
    Args:
        telegram_id: Telegram user ID
        message_id: Telegram message ID
    """
    key = (telegram_id, message_id)
    now = datetime.now(timezone.utc)
    _processed_messages[key] = now
    
    logger.debug(f"Marked message {message_id} from user {telegram_id} as processed")
    
    # Clean up old entries
    _cleanup_cache()


def _cleanup_cache() -> None:
    """
    Remove expired entries from the cache to prevent memory leaks.
    Called automatically when marking new messages as processed.
    """
    now = datetime.now(timezone.utc)
    expiry_threshold = now - timedelta(hours=CACHE_EXPIRY_HOURS)
    
    # Find expired keys
    expired_keys = [
        key for key, timestamp in _processed_messages.items()
        if timestamp < expiry_threshold
    ]
    
    # Remove expired entries
    for key in expired_keys:
        del _processed_messages[key]
    
    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


def get_cache_stats() -> Dict[str, int]:
    """
    Get statistics about the message cache.
    
    Returns:
        Dictionary with cache statistics
    """
    return {
        "total_entries": len(_processed_messages),
        "cache_expiry_hours": CACHE_EXPIRY_HOURS
    }


def clear_cache() -> None:
    """
    Clear all entries from the cache.
    Useful for testing and debugging.
    """
    _processed_messages.clear()
    logger.info("Message cache cleared")
