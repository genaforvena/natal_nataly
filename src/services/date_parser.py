"""
Date parser for transit requests.
Uses LLM to extract dates from natural language, similar to birth data extraction.
"""

import logging
from datetime import datetime, timezone, timedelta
from src.llm import extract_transit_date

logger = logging.getLogger(__name__)


def parse_transit_date(text: str) -> datetime:
    """
    Parse date from user text for transit calculations using LLM.
    
    Uses LLM to extract date from natural language, similar to how birth data is extracted.
    This provides better support for various formats and languages.
    
    Args:
        text: User's message text
        
    Returns:
        datetime object in UTC timezone. Defaults to current UTC if no date found.
    """
    logger.debug(f"Parsing transit date from text: {text[:100]}...")
    
    try:
        # Use LLM to extract date
        date_data = extract_transit_date(text)
        date_str = date_data.get("date")
        
        if not date_str:
            # No date specified or "now" - use current UTC
            logger.info("No date specified or 'now' detected, using current UTC time")
            return datetime.now(timezone.utc)
        
        # Handle relative dates
        if date_str == "tomorrow":
            logger.info("Relative date: tomorrow")
            return datetime.now(timezone.utc) + timedelta(days=1)
        elif date_str == "next_month":
            logger.info("Relative date: next month")
            now = datetime.now(timezone.utc)
            # Move to first day of next month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1, 12, 0, tzinfo=timezone.utc)
            else:
                return datetime(now.year, now.month + 1, 1, 12, 0, tzinfo=timezone.utc)
        elif date_str == "yesterday":
            logger.info("Relative date: yesterday")
            return datetime.now(timezone.utc) - timedelta(days=1)
        
        # Parse absolute date (YYYY-MM-DD format from LLM)
        try:
            # LLM should return dates in YYYY-MM-DD format
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            # Set to noon UTC
            result = datetime(parsed_date.year, parsed_date.month, parsed_date.day, 12, 0, tzinfo=timezone.utc)
            logger.info(f"Parsed date from LLM: {result.isoformat()}")
            return result
        except ValueError as e:
            logger.warning(f"Failed to parse date '{date_str}' from LLM: {e}")
            # Fallback to current UTC
            return datetime.now(timezone.utc)
    
    except Exception as e:
        logger.exception(f"Error in LLM-based date parsing: {e}")
        # Fallback to current UTC
        logger.warning("Falling back to current UTC time due to error")
        return datetime.now(timezone.utc)
