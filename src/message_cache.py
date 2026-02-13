"""
Persistent cache for tracking processed Telegram messages.

This module implements a hybrid caching system:
1. In-memory cache for fast lookups (performance)
2. Database-backed storage for persistence across restarts (reliability)

This prevents duplicate processing when:
- Multiple webhooks arrive concurrently (in-memory lock)
- Application restarts while Telegram retries webhooks (database persistence)
"""

import logging
import random
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from src.db import SessionLocal
from src.models import ProcessedMessage

logger = logging.getLogger(__name__)

# In-memory cache: (telegram_id, message_id) -> timestamp
# Provides fast lookups without database queries
_processed_messages: Dict[Tuple[str, int], datetime] = {}

# Thread lock for cache access
_cache_lock = threading.RLock()

# Cache configuration
CACHE_EXPIRY_HOURS = 24  # How long to keep entries in cache
DB_EXPIRY_DAYS = 7  # Keep database entries for 7 days to handle long Telegram retry windows


def mark_if_new(telegram_id: str, message_id: int) -> bool:
    """
    Atomically check if a message is new and mark it as processed.
    
    Uses hybrid caching:
    1. Check in-memory cache first (fast)
    2. Check database if not in memory (persistent)
    3. Mark in both cache and database if new
    
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
    db_expiry_threshold = now - timedelta(days=DB_EXPIRY_DAYS)
    
    with _cache_lock:
        # Step 1: Check in-memory cache first (fast path)
        if key in _processed_messages:
            processed_time = _processed_messages[key]
            
            # Check if entry is expired
            if processed_time < expiry_threshold:
                # Entry is expired, remove it and check database
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
                    "Message %s from user %s was already processed at %s (in-memory cache hit)",
                    message_id,
                    telegram_id,
                    processed_time,
                )
                return False
        
        # Step 2: Check database for persistence across restarts
        session = SessionLocal()
        try:
            existing = session.query(ProcessedMessage).filter_by(
                telegram_id=telegram_id,
                message_id=message_id
            ).first()
            
            if existing:
                # Check if database entry is expired
                # Handle both timezone-aware and naive datetimes from database
                existing_time = existing.processed_at
                if existing_time.tzinfo is None:
                    # Database returned naive datetime, assume UTC
                    existing_time = existing_time.replace(tzinfo=timezone.utc)
                
                if existing_time < db_expiry_threshold:
                    # Entry is expired, delete it and treat as new
                    session.delete(existing)
                    session.commit()
                    logger.debug(
                        "Expired database entry for message %s from user %s "
                        "(processed at %s)",
                        message_id,
                        telegram_id,
                        existing.processed_at,
                    )
                else:
                    # Entry is valid - this is a duplicate
                    logger.info(
                        "Message %s from user %s was already processed at %s (database hit, likely post-restart)",
                        message_id,
                        telegram_id,
                        existing_time,
                    )
                    # Update in-memory cache to speed up future checks
                    _processed_messages[key] = existing_time
                    return False
            
            # Step 3: Message is new - mark it in both cache and database
            # Add to database
            new_entry = ProcessedMessage(
                telegram_id=telegram_id,
                message_id=message_id,
                processed_at=now
            )
            session.add(new_entry)
            try:
                session.commit()
            except Exception as commit_error:
                # Handle unique constraint violation (race condition where another process inserted)
                session.rollback()
                error_msg = str(commit_error).lower()
                if 'unique' in error_msg or 'duplicate' in error_msg:
                    logger.info(
                        "Message %s from user %s already exists in database (race condition), "
                        "treating as duplicate",
                        message_id,
                        telegram_id
                    )
                    return False
                else:
                    # Other database error, re-raise to be caught by outer exception handler
                    raise
            
            # Add to in-memory cache
            _processed_messages[key] = now
            
            logger.debug(
                "Marked message %s from user %s as processed in cache and database",
                message_id,
                telegram_id,
            )
            
            # Clean up old entries periodically
            _cleanup_cache_and_db_locked(session)
            
            return True
            
        except Exception as e:
            logger.exception(f"Error checking/marking message in database: {e}")
            session.rollback()
            # If database fails, fall back to in-memory only (better than nothing)
            _processed_messages[key] = now
            logger.warning(
                "Database check failed for message %s, marked in memory only",
                message_id
            )
            return True
        finally:
            session.close()



def _cleanup_cache_and_db_locked(session: Session) -> None:
    """
    Remove expired entries from both cache and database to prevent memory/storage leaks.
    Called automatically when marking new messages as processed.
    
    NOTE: This function assumes the caller already holds _cache_lock.
    
    Args:
        session: Active database session to use for cleanup
    """
    now = datetime.now(timezone.utc)
    memory_expiry_threshold = now - timedelta(hours=CACHE_EXPIRY_HOURS)
    db_expiry_threshold = now - timedelta(days=DB_EXPIRY_DAYS)
    
    # Clean up in-memory cache
    expired_keys = [
        key for key, timestamp in _processed_messages.items()
        if timestamp < memory_expiry_threshold
    ]
    
    for key in expired_keys:
        del _processed_messages[key]
    
    if expired_keys:
        logger.debug("Cleaned up %d expired in-memory cache entries", len(expired_keys))
    
    # Clean up database (only occasionally to avoid overhead)
    # Use a simple heuristic: clean every 100th call
    if random.randint(1, 100) == 1:
        try:
            deleted_count = session.query(ProcessedMessage).filter(
                ProcessedMessage.processed_at < db_expiry_threshold
            ).delete()
            session.commit()
            
            if deleted_count > 0:
                logger.info("Cleaned up %d expired database entries", deleted_count)
        except Exception as e:
            logger.warning(f"Error cleaning up database entries: {e}")
            session.rollback()



def get_cache_stats() -> Dict[str, int]:
    """
    Get statistics about the message cache.
    
    Returns:
        Dictionary with cache statistics including both memory and database
    """
    with _cache_lock:
        stats = {
            "memory_entries": len(_processed_messages),
            "cache_expiry_hours": CACHE_EXPIRY_HOURS,
            "db_expiry_days": DB_EXPIRY_DAYS
        }
        
        # Get database count
        try:
            session = SessionLocal()
            try:
                db_count = session.query(ProcessedMessage).count()
                stats["db_entries"] = db_count
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"Could not get database stats: {e}")
            stats["db_entries"] = -1
        
        return stats


def clear_cache() -> None:
    """
    Clear all entries from the cache and database.
    Useful for testing and debugging.
    
    WARNING: This will allow previously processed messages to be processed again!
    """
    with _cache_lock:
        # Clear in-memory cache
        _processed_messages.clear()
        logger.info("In-memory message cache cleared")
        
        # Clear database
        try:
            session = SessionLocal()
            try:
                deleted_count = session.query(ProcessedMessage).delete()
                session.commit()
                logger.info(f"Database message cache cleared ({deleted_count} entries)")
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error clearing database cache: {e}")

