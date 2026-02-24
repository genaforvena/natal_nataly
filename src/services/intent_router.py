"""
Intent detection for natural language routing.

Uses lightweight keyword/heuristic matching to classify user messages,
eliminating the extra LLM round-trip that previously added latency before
every response.

Maps to simplified routing categories:
- provide_birth_data patterns → birth_input
- profile switch patterns     → change_profile
- everything else             → natal_question (handled by single LLM call)
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

IntentType = Literal["birth_input", "change_profile", "natal_question"]

# Patterns that indicate the user is supplying birth data
_BIRTH_DATA_PATTERNS = [
    "dob:", "date of birth", "birth date", "born on",
    "lat:", "lng:", "time:", "координаты", "дата рождения",
    "место рождения", "время рождения",
]

# Patterns that indicate the user wants to switch active profile
_PROFILE_SWITCH_PATTERNS = [
    "переключись", "switch to", "change profile", "смени профиль",
    "активируй профиль", "выбери профиль", "switch profile",
]


def detect_request_type(user_text: str) -> IntentType:
    """
    Detect the type of user request using lightweight keyword matching.

    This is intentionally simple: the single downstream LLM call handles
    everything that isn't explicitly birth data input or profile switching.

    Args:
        user_text: User's message text

    Returns:
        One of: "birth_input", "change_profile", "natal_question"
    """
    text_lower = user_text.lower()

    if any(p in text_lower for p in _BIRTH_DATA_PATTERNS):
        logger.info("Intent detected: birth_input (keyword match)")
        return "birth_input"

    if any(p in text_lower for p in _PROFILE_SWITCH_PATTERNS):
        logger.info("Intent detected: change_profile (keyword match)")
        return "change_profile"

    logger.debug("Intent detected: natal_question (default)")
    return "natal_question"


async def detect_request_type_async(user_text: str) -> IntentType:
    """
    Async version of detect_request_type.

    No I/O is performed so this is synchronous in practice; the async
    signature is kept for API compatibility with existing call-sites.
    """
    return detect_request_type(user_text)
