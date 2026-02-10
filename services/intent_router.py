"""
Intent detection for natural language routing.
LLM-based detection to determine if user wants:
- provide_birth_data: User providing birth data
- ask_about_chart: Question about their natal chart  
- ask_transit_question: Question about transits (current or future)
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

IntentType = Literal["birth_input", "natal_question", "transit_question"]


def detect_request_type(user_text: str) -> IntentType:
    """
    Detect the type of user request using LLM-based classification.
    
    Uses the existing classify_intent() function from llm.py which now includes
    the ask_transit_question intent. Maps the LLM response to our simplified
    intent types.
    
    Args:
        user_text: User's message text
        
    Returns:
        One of: "birth_input", "natal_question", "transit_question"
    """
    from llm import classify_intent
    
    logger.debug(f"Detecting intent for message: {user_text[:100]}...")
    
    try:
        # Use LLM to classify intent
        intent_result = classify_intent(user_text)
        llm_intent = intent_result.get("intent", "unknown")
        confidence = intent_result.get("confidence", 0.0)
        
        logger.info(f"LLM classified intent as: {llm_intent} (confidence: {confidence})")
        
        # Map LLM intent to our simplified intent types
        if llm_intent == "provide_birth_data":
            logger.info("Intent detected: birth_input")
            return "birth_input"
        elif llm_intent == "ask_transit_question":
            logger.info("Intent detected: transit_question")
            return "transit_question"
        elif llm_intent in ["ask_about_chart", "ask_general_question", "meta_conversation", 
                           "clarify_birth_data", "new_profile_request", "switch_profile"]:
            # All other intents are treated as natal questions for routing purposes
            logger.info("Intent detected: natal_question")
            return "natal_question"
        else:
            # Unknown or low confidence - default to natal question
            logger.info("Intent detected: natal_question (default for unknown intent)")
            return "natal_question"
            
    except Exception as e:
        logger.exception(f"Error in LLM intent detection: {e}")
        # Fallback to natal_question on error
        logger.warning("Falling back to natal_question due to error")
        return "natal_question"
