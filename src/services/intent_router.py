"""
Intent detection for natural language routing.
LLM-based detection using classify_intent() from llm.py.

Maps detailed LLM intents to simplified routing categories:
- provide_birth_data (LLM) → birth_input (routing)
- change_profile (LLM) → change_profile (routing)
- all other intents → natal_question (routing)

Note: Transit functionality has been temporarily disabled.
"""

import logging
from typing import Literal
from src.llm import classify_intent, classify_intent_async

logger = logging.getLogger(__name__)

IntentType = Literal["birth_input", "change_profile", "natal_question"]


def detect_request_type(user_text: str) -> IntentType:
    """
    Detect the type of user request using LLM-based classification.
    
    Calls classify_intent() which returns detailed LLM intents like:
    - provide_birth_data
    - ask_about_chart
    - ask_general_question
    - meta_conversation
    - change_profile
    - etc.
    
    These are mapped to simplified routing categories:
    - provide_birth_data → birth_input
    - change_profile → change_profile
    - all others → natal_question
    
    Note: Transit functionality has been temporarily disabled.
    
    Args:
        user_text: User's message text
        
    Returns:
        One of: "birth_input", "change_profile", "natal_question"
    """
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
        elif llm_intent == "change_profile":
            logger.info("Intent detected: change_profile")
            return "change_profile"
        else:
            # All other intents default to natal_question
            # This includes: ask_about_chart, ask_general_question, meta_conversation,
            # clarify_birth_data, new_profile_request, unknown
            # Note: ask_transit_question is also mapped to natal_question (transit functionality disabled)
            logger.info(f"Intent detected: natal_question (mapped from {llm_intent})")
            return "natal_question"
            
    except Exception as e:
        logger.exception(f"Error in LLM intent detection: {e}")
        # Fallback to natal_question on error
        logger.warning("Falling back to natal_question due to error")
        return "natal_question"


async def detect_request_type_async(user_text: str) -> IntentType:
    """
    Async version of detect_request_type that uses non-blocking LLM calls.
    
    See detect_request_type() for full documentation.
    """
    logger.debug(f"Detecting intent for message: {user_text[:100]}...")
    
    try:
        # Use async LLM to classify intent
        intent_result = await classify_intent_async(user_text)
        llm_intent = intent_result.get("intent", "unknown")
        confidence = intent_result.get("confidence", 0.0)
        
        logger.info(f"LLM classified intent as: {llm_intent} (confidence: {confidence})")
        
        # Map LLM intent to simplified routing categories
        if llm_intent == "provide_birth_data":
            logger.info("Intent detected: birth_input")
            return "birth_input"
        elif llm_intent == "change_profile":
            logger.info("Intent detected: change_profile")
            return "change_profile"
        else:
            # All other intents default to natal_question
            logger.info(f"Intent detected: natal_question (mapped from {llm_intent})")
            return "natal_question"
            
    except Exception as e:
        logger.exception(f"Error in LLM intent detection: {e}")
        # Fallback to natal_question on error
        logger.warning("Falling back to natal_question due to error")
        return "natal_question"
