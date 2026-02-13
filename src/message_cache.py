"""
Runtime cache for tracking processed Telegram messages.

This module implements a simple in-memory cache to prevent duplicate processing
of the same message when Telegram webhooks are triggered multiple times.
"""

import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# In-memory cache: (telegram_id, message_id) -> timestamp
# Stores when each message was last processed
_processed_messages: Dict[Tuple[str, int], datetime] = {}

# Thread lock for cache access
_cache_lock = threading.RLock()

# Cache configuration
CACHE_EXPIRY_HOURS = 24  # How long to keep entries in cache


def mark_if_new(telegram_id: str, message_id: int) -> bool:
    """
    Atomically check if a message is new and mark it as processed.
    
    This operation is atomic to prevent race conditions when multiple
    webhook requests arrive concurrently for the same message.
    
    Args:
        telegram_id: Telegram user ID
        message_id: Telegram message ID
        
    Returns:
        True if the message was new and has been marked as processed,
        False if the message was already processed (duplicate)
    """
    key = (telegram_id, message_id)
    now = datetime.now(timezone.utc)
    expiry_threshold = now - timedelta(hours=CACHE_EXPIRY_HOURS)
    
    with _cache_lock:
        # Check if message exists and is not expired
        if key in _processed_messages:
            processed_time = _processed_messages[key]
            
            # Check if entry is expired
            if processed_time < expiry_threshold:
                # Entry is expired, remove it and treat as new
                del _processed_messages[key]
                logger.debug(
                    "Expired cache entry for message %s from user %s "
                    "(processed at %s, expired at %s)",
                    message_id,
                    telegram_id,
                    processed_time,
                    expiry_threshold,
                )
            else:
                # Entry is valid - this is a duplicate
                logger.debug(
                    "Message %s from user %s was already processed at %s",
                    message_id,
                    telegram_id,
                    processed_time,
                )
                return False
        
        # Message is new, mark it as processed
        _processed_messages[key] = now
        logger.debug(
            "Marked message %s from user %s as processed",
            message_id,
            telegram_id,
        )
        
        # Clean up old entries periodically
        _cleanup_cache_locked()
        
        return True


def _cleanup_cache_locked() -> None:
    """
    Remove expired entries from the cache to prevent memory leaks.
    Called automatically when marking new messages as processed.
    
    NOTE: This function assumes the caller already holds _cache_lock.
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
        logger.debug("Cleaned up %d expired cache entries", len(expired_keys))


def get_cache_stats() -> Dict[str, int]:
    """
    Get statistics about the message cache.
    
    Returns:
        Dictionary with cache statistics
    """
    with _cache_lock:
        return {
            "total_entries": len(_processed_messages),
            "cache_expiry_hours": CACHE_EXPIRY_HOURS
        }


def clear_cache() -> None:
    """
    Clear all entries from the cache.
    Useful for testing and debugging.
    """
    with _cache_lock:
        _processed_messages.clear()
    logger.info("Message cache cleared")
