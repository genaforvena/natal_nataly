"""
Intent detection for natural language routing.
LLM-based detection using classify_intent() from llm.py.

Maps detailed LLM intents to simplified routing categories:
- provide_birth_data (LLM) → birth_input (routing)
- all other intents → natal_question (routing)

Note: Transit functionality has been temporarily disabled.
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

IntentType = Literal["birth_input", "natal_question"]


def detect_request_type(user_text: str) -> IntentType:
    """
    Detect the type of user request using LLM-based classification.
    
    Calls classify_intent() which returns detailed LLM intents like:
    - provide_birth_data
    - ask_about_chart
    - ask_general_question
    - meta_conversation
    - etc.
    
    These are mapped to simplified routing categories:
    - provide_birth_data → birth_input
    - all others → natal_question
    
    Note: Transit functionality has been temporarily disabled.
    
    Args:
        user_text: User's message text
        
    Returns:
        One of: "birth_input", "natal_question"
    """
    from llm import classify_intent
    
    logger.debug(f"Detecting intent for message: {user_text[:100]}...")
    
    try:
        # Use LLM to classify intent
        intent_result = classify_intent(user_text)
        llm_intent = intent_result.get("intent", "unknown")
        confidence = intent_result.get("confidence", 0.0)
        
        logger.info(f"LLM classified intent as: {llm_intent} (confidence: {confidence})")
        
        # Map LLM intent to simplified routing categories
        if llm_intent == "provide_birth_data":
            logger.info("Intent detected: birth_input")
            return "birth_input"
        else:
            # All other intents default to natal_question
            # This includes: ask_about_chart, ask_general_question, meta_conversation,
            # clarify_birth_data, new_profile_request, switch_profile, unknown
            # Note: ask_transit_question is also mapped to natal_question (transit functionality disabled)
            logger.info(f"Intent detected: natal_question (mapped from {llm_intent})")
            return "natal_question"
            
    except Exception as e:
        logger.exception(f"Error in LLM intent detection: {e}")
        # Fallback to natal_question on error
        logger.warning("Falling back to natal_question due to error")
        return "natal_question"
