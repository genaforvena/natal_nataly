"""
Message throttling module to prevent spam and improve user experience.

This module implements a 15-second throttling window:
- If multiple messages arrive within 15 seconds from the same user, they are grouped
- The bot responds once with all grouped messages combined
- This prevents response flooding and provides a better user experience
"""

import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Throttling window in seconds
THROTTLE_WINDOW_SECONDS = 15

# Structure: {telegram_id: (last_message_time, [pending_messages])}
_user_message_groups: Dict[str, Tuple[datetime, List[str]]] = {}

# Thread lock for thread-safe access
_throttle_lock = threading.RLock()


def should_process_message(telegram_id: str, message_text: str) -> Tuple[bool, List[str]]:
    """
    Determine if a message should be processed immediately or throttled.
    
    This function implements a 15-second throttling window:
    - If this is the first message from the user, process it immediately
    - If a message arrives within 15 seconds of the previous one, add it to the group
    - If 15+ seconds have passed, process the accumulated group and start a new one
    
    Args:
        telegram_id: Telegram user ID
        message_text: The message text content
        
    Returns:
        Tuple of (should_process, messages_to_process):
        - should_process: True if we should process now, False if throttling
        - messages_to_process: List of messages to process (empty if throttling)
    """
    now = datetime.now(timezone.utc)
    
    with _throttle_lock:
        if telegram_id not in _user_message_groups:
            # First message from this user - start a new group but process immediately
            _user_message_groups[telegram_id] = (now, [])
            logger.debug(f"First message from user {telegram_id}, processing immediately")
            return True, [message_text]
        
        last_time, pending_messages = _user_message_groups[telegram_id]
        time_since_last = (now - last_time).total_seconds()
        
        if time_since_last < THROTTLE_WINDOW_SECONDS:
            # Within throttle window - add to pending group
            pending_messages.append(message_text)
            _user_message_groups[telegram_id] = (now, pending_messages)
            logger.info(
                f"Message from user {telegram_id} throttled "
                f"({time_since_last:.1f}s since last, {len(pending_messages)} pending)"
            )
            return False, []
        else:
            # Throttle window expired - process accumulated messages
            if pending_messages:
                # There are pending messages, include them with this new one
                all_messages = pending_messages + [message_text]
                logger.info(
                    f"Throttle window expired for user {telegram_id}, "
                    f"processing {len(all_messages)} grouped messages"
                )
                # Reset for next group
                _user_message_groups[telegram_id] = (now, [])
                return True, all_messages
            else:
                # No pending messages, just process this one
                _user_message_groups[telegram_id] = (now, [])
                logger.debug(f"Throttle window expired for user {telegram_id}, processing single message")
                return True, [message_text]


def clear_user_throttle(telegram_id: str) -> None:
    """
    Clear throttling state for a specific user.
    Useful after processing a message group or for testing.
    
    Args:
        telegram_id: Telegram user ID
    """
    with _throttle_lock:
        if telegram_id in _user_message_groups:
            del _user_message_groups[telegram_id]
            logger.debug(f"Cleared throttle state for user {telegram_id}")


def get_throttle_stats() -> Dict[str, any]:
    """
    Get statistics about message throttling.
    
    Returns:
        Dictionary with throttling statistics
    """
    with _throttle_lock:
        total_users = len(_user_message_groups)
        users_with_pending = sum(
            1 for _, (_, pending) in _user_message_groups.items()
            if pending
        )
        total_pending = sum(
            len(pending) for _, (_, pending) in _user_message_groups.items()
        )
        
        return {
            "throttle_window_seconds": THROTTLE_WINDOW_SECONDS,
            "active_users": total_users,
            "users_with_pending_messages": users_with_pending,
            "total_pending_messages": total_pending
        }


def clear_all_throttles() -> None:
    """
    Clear all throttling state.
    Useful for testing and debugging.
    
    WARNING: This will reset all throttle windows!
    """
    with _throttle_lock:
        count = len(_user_message_groups)
        _user_message_groups.clear()
        logger.info(f"Cleared throttle state for {count} users")
