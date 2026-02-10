"""
Date parser for transit requests.
Supports various date formats and natural language expressions.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Month name mappings (Russian and English)
MONTH_NAMES = {
    # English
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
    
    # Russian
    "январь": 1, "января": 1, "январе": 1, "январ": 1,
    "февраль": 2, "февраля": 2, "феврале": 2, "феврал": 2,
    "март": 3, "марта": 3, "марте": 3,
    "апрель": 4, "апреля": 4, "апреле": 4, "апрел": 4,
    "май": 5, "мая": 5, "мае": 5,
    "июнь": 6, "июня": 6, "июне": 6, "июн": 6,
    "июль": 7, "июля": 7, "июле": 7, "июл": 7,
    "август": 8, "августа": 8, "августе": 8,
    "сентябрь": 9, "сентября": 9, "сентябре": 9, "сентябр": 9,
    "октябрь": 10, "октября": 10, "октябре": 10, "октябр": 10,
    "ноябрь": 11, "ноября": 11, "ноябре": 11, "ноябр": 11,
    "декабрь": 12, "декабря": 12, "декабре": 12, "декабр": 12,
}


def parse_transit_date(text: str) -> datetime:
    """
    Parse date from user text for transit calculations.
    
    Supports:
    - ISO format: 2026-03-01
    - European format: 01.03.2026
    - Natural language: "march 2026", "март 2026"
    - "now", "today", "сейчас" -> current UTC time
    
    Args:
        text: User's message text
        
    Returns:
        datetime object in UTC timezone. Defaults to current UTC if no date found.
    """
    text_lower = text.lower().strip()
    
    logger.debug(f"Parsing transit date from text: {text_lower[:100]}...")
    
    # Check for "now", "today", "сейчас"
    now_keywords = ["now", "today", "сейчас", "текущ"]
    for keyword in now_keywords:
        if keyword in text_lower:
            logger.info("Using current UTC time (keyword: now/today)")
            return datetime.now(timezone.utc)
    
    # Try to parse ISO format: YYYY-MM-DD
    iso_pattern = r'\b(\d{4})-(\d{2})-(\d{2})\b'
    iso_match = re.search(iso_pattern, text)
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        try:
            dt = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
            logger.info(f"Parsed ISO date: {dt.isoformat()}")
            return dt
        except ValueError as e:
            logger.warning(f"Invalid ISO date: {e}")
    
    # Try to parse European format: DD.MM.YYYY
    euro_pattern = r'\b(\d{2})\.(\d{2})\.(\d{4})\b'
    euro_match = re.search(euro_pattern, text)
    if euro_match:
        day, month, year = map(int, euro_match.groups())
        try:
            dt = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
            logger.info(f"Parsed European date: {dt.isoformat()}")
            return dt
        except ValueError as e:
            logger.warning(f"Invalid European date: {e}")
    
    # Try to parse natural language: "march 2026", "март 2026"
    for month_name, month_num in MONTH_NAMES.items():
        # Pattern: month_name YYYY
        pattern = rf'\b{re.escape(month_name)}\s+(\d{{4}})\b'
        match = re.search(pattern, text_lower)
        if match:
            year = int(match.group(1))
            try:
                # Use first day of the month
                dt = datetime(year, month_num, 1, 12, 0, tzinfo=timezone.utc)
                logger.info(f"Parsed natural language date: {dt.isoformat()} (month: {month_name})")
                return dt
            except ValueError as e:
                logger.warning(f"Invalid natural language date: {e}")
        
        # Pattern: YYYY month_name (e.g., "2026 март")
        pattern = rf'\b(\d{{4}})\s+{re.escape(month_name)}\b'
        match = re.search(pattern, text_lower)
        if match:
            year = int(match.group(1))
            try:
                dt = datetime(year, month_num, 1, 12, 0, tzinfo=timezone.utc)
                logger.info(f"Parsed natural language date: {dt.isoformat()} (month: {month_name})")
                return dt
            except ValueError as e:
                logger.warning(f"Invalid natural language date: {e}")
    
    # Try to extract just a year (YYYY)
    year_pattern = r'\b(202[4-9]|203[0-9])\b'
    year_match = re.search(year_pattern, text)
    if year_match:
        year = int(year_match.group(1))
        dt = datetime(year, 1, 1, 12, 0, tzinfo=timezone.utc)
        logger.info(f"Parsed year only: {dt.isoformat()}")
        return dt
    
    # Default: current UTC time
    logger.info("No date found in text, using current UTC time")
    return datetime.now(timezone.utc)
