"""
Intent detection for natural language routing.
Rule-based detection (no LLM) to determine if user wants:
- birth_input: User providing birth data
- natal_question: Question about their natal chart
- transit_question: Question about transits (current or future)
"""

import logging
import re
from typing import Literal

logger = logging.getLogger(__name__)

IntentType = Literal["birth_input", "natal_question", "transit_question"]

# Keywords indicating transit questions (Russian + English)
TRANSIT_KEYWORDS = [
    # Russian keywords
    "транзит", "transit",
    "сейчас", "now", "today",
    "будущее", "future",
    "что происходит", "what's happening", "what is happening",
    "как выглядит", "how does",
    "текущ", "current",  # текущий, текущая, текущие
    "настоящ",  # настоящий, настоящее время
    "прогноз", "forecast", "prediction",
    # Month names in Russian and English
    "январ", "january", "jan",
    "феврал", "february", "feb",
    "март", "march", "mar",
    "апрел", "april", "apr",
    "май", "may",
    "июн", "june", "jun",
    "июл", "july", "jul",
    "август", "august", "aug",
    "сентябр", "september", "sep",
    "октябр", "october", "oct",
    "ноябр", "november", "nov",
    "декабр", "december", "dec",
    # Time-related keywords
    "этот", "this",  # этот месяц, this month
    "следующ", "next",  # следующий месяц, next month
    "завтра", "tomorrow",
    "вчера", "yesterday",
    "неделя", "week",
    "месяц", "month",
    "год", "year",
]

# Phrases that specifically indicate transit questions (more specific)
TRANSIT_PHRASES = [
    "что делает",  # что делает сатурн
    "what does",  # what does saturn do
    "how does",  # how does march look
]

# Keywords indicating birth data input
BIRTH_DATA_KEYWORDS = [
    "dob:", "time:", "lat:", "lng:",
    "родился", "родилась", "born",
    "дата рождения", "birth date", "date of birth",
    "место рождения", "place of birth", "birth place",
]


def detect_request_type(user_text: str) -> IntentType:
    """
    Detect the type of user request based on keywords and patterns.
    
    Rule-based detection (no LLM):
    1. If contains birth data fields (DOB:, Time:, Lat:, Lng:) -> birth_input
    2. If contains transit/time keywords -> transit_question
    3. Otherwise -> natal_question
    
    Args:
        user_text: User's message text
        
    Returns:
        One of: "birth_input", "natal_question", "transit_question"
    """
    text_lower = user_text.lower().strip()
    
    logger.debug(f"Detecting intent for message: {text_lower[:100]}...")
    
    # Check for birth data input (highest priority)
    for keyword in BIRTH_DATA_KEYWORDS:
        if keyword.lower() in text_lower:
            logger.info(f"Intent detected: birth_input (keyword: {keyword})")
            return "birth_input"
    
    # Check for structured birth data format (DOB:, Time:, Lat:, Lng:)
    has_dob = re.search(r'\bdob\s*:', text_lower)
    has_time = re.search(r'\btime\s*:', text_lower)
    has_lat = re.search(r'\blat\s*:', text_lower)
    has_lng = re.search(r'\blng\s*:', text_lower)
    
    if has_dob or has_time or has_lat or has_lng:
        logger.info("Intent detected: birth_input (structured format)")
        return "birth_input"
    
    # Check for specific transit phrases first (more specific matching)
    for phrase in TRANSIT_PHRASES:
        if phrase.lower() in text_lower:
            # Additional check: make sure it's about a planet or time period
            # Look for planet names or time references nearby
            planets = ["saturn", "jupiter", "mars", "venus", "mercury", "moon", "sun", 
                      "uranus", "neptune", "pluto",
                      "сатурн", "юпитер", "марс", "венер", "меркурий", "луна", "солнц",
                      "уран", "нептун", "плутон"]
            time_refs = ["сейчас", "now", "март", "march", "месяц", "month", "future", "будущ"]
            
            # For "what does" or "что делает", require time reference, not just planet name
            # This prevents "what does my moon mean" from being a transit question
            if phrase in ["what does", "что делает"]:
                # Must have explicit time reference
                has_time_ref = any(ref in text_lower for ref in time_refs)
                if has_time_ref:
                    logger.info(f"Intent detected: transit_question (phrase: {phrase} with time ref)")
                    return "transit_question"
            else:
                # For other phrases like "how does", check for planet or time
                has_planet_or_time = any(ref in text_lower for ref in planets + time_refs)
                if has_planet_or_time:
                    logger.info(f"Intent detected: transit_question (phrase: {phrase})")
                    return "transit_question"
    
    # Check for general transit keywords
    for keyword in TRANSIT_KEYWORDS:
        if keyword.lower() in text_lower:
            logger.info(f"Intent detected: transit_question (keyword: {keyword})")
            return "transit_question"
    
    # Check for date patterns (YYYY-MM-DD, DD.MM.YYYY)
    date_pattern = r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}\.\d{2}\.\d{4}\b'
    if re.search(date_pattern, text_lower):
        logger.info("Intent detected: transit_question (date pattern found)")
        return "transit_question"
    
    # Check for year patterns (e.g., "2026", "2027") which often indicate transit questions
    year_pattern = r'\b20[2-9]\d\b'
    if re.search(year_pattern, text):
        logger.info("Intent detected: transit_question (year pattern found)")
        return "transit_question"
    
    # Default to natal question
    logger.info("Intent detected: natal_question (default)")
    return "natal_question"
