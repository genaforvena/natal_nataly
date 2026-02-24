"""
Session Manager - Conversation context stored as JSON in User model.

Replaces the ConversationThread DB-row-per-message approach with a simple
JSON array stored directly on the User record.  Capped at MAX_SESSION_MESSAGES
entries (last N messages, FIFO eviction).

Format:
    [
        {"role": "user",      "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
"""

import json
import logging
from sqlalchemy.orm import Session
from src.models import User

logger = logging.getLogger(__name__)

MAX_SESSION_MESSAGES = 20


def get_session_context(user: User) -> list:
    """
    Load conversation context from User.conversation_session_json.

    Args:
        user: User ORM object

    Returns:
        List of message dicts [{"role": ..., "content": ...}], oldest first.
        Returns empty list if no context is stored or on parse error.
    """
    if not user.conversation_session_json:
        return []
    try:
        context = json.loads(user.conversation_session_json)
        if isinstance(context, list):
            logger.debug(
                "Loaded session context for %s: %d messages",
                user.telegram_id,
                len(context),
            )
            return context
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning(
            "Could not parse conversation_session_json for %s: %s",
            user.telegram_id,
            exc,
        )
    return []


def update_session_context(
    session: Session,
    user: User,
    new_messages: list,
    max_messages: int = MAX_SESSION_MESSAGES,
) -> None:
    """
    Append new_messages to the user's conversation context and persist.

    Truncates to the last `max_messages` entries (FIFO eviction).

    Args:
        session:      Active SQLAlchemy session.
        user:         User ORM object (will be mutated).
        new_messages: List of {"role", "content"} dicts to append.
        max_messages: Cap on total messages kept (default MAX_SESSION_MESSAGES).
    """
    existing = get_session_context(user)
    combined = existing + new_messages
    if len(combined) > max_messages:
        combined = combined[-max_messages:]
    user.conversation_session_json = json.dumps(combined, ensure_ascii=False)
    session.commit()
    logger.debug(
        "Updated session context for %s: %d messages total",
        user.telegram_id,
        len(combined),
    )


def reset_session_context(session: Session, user: User) -> None:
    """
    Clear the conversation context for a user.

    Args:
        session: Active SQLAlchemy session.
        user:    User ORM object.
    """
    user.conversation_session_json = None
    session.commit()
    logger.info("Session context reset for %s", user.telegram_id)
