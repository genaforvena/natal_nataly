import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from src.db import SessionLocal
from src.models import AnalyticsEvent

logger = logging.getLogger(__name__)

class AnalyticsProvider(ABC):
    @abstractmethod
    def capture(self, user_id: str, event_name: str, properties: Optional[Dict[str, Any]] = None):
        pass

    @abstractmethod
    def identify(self, user_id: str, properties: Optional[Dict[str, Any]] = None):
        pass

class ConsoleProvider(AnalyticsProvider):
    def capture(self, user_id: str, event_name: str, properties: Optional[Dict[str, Any]] = None):
        logger.info(f"[ANALYTICS] Event: {event_name} | User: {user_id} | Props: {properties}")

    def identify(self, user_id: str, properties: Optional[Dict[str, Any]] = None):
        logger.info(f"[ANALYTICS] Identify User: {user_id} | Props: {properties}")

class SQLProvider(AnalyticsProvider):
    """
    In-house SQL-based analytics provider.
    Stores events directly in the database for maximum privacy and data ownership.
    """
    def capture(self, user_id: str, event_name: str, properties: Optional[Dict[str, Any]] = None):
        try:
            session = SessionLocal()
            try:
                event = AnalyticsEvent(
                    telegram_id=user_id,
                    event_name=event_name,
                    properties=json.dumps(properties) if properties else None
                )
                session.add(event)
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to capture SQL analytics event: {e}")

    def identify(self, user_id: str, properties: Optional[Dict[str, Any]] = None):
        # Identify is handled by updating user properties in the database
        # This can be implemented by adding custom fields to the User model if needed.
        # For now, we track it as a special event.
        self.capture(user_id, "$identify", properties)

class AnalyticsService:
    _instance: Optional['AnalyticsService'] = None

    def __init__(self):
        """Initialize the AnalyticsService with a SQLProvider."""
        # Default to SQLProvider for in-house analytics as per user preference
        self.provider: AnalyticsProvider = SQLProvider()
        logger.info("Analytics initialized with SQLProvider (In-house)")

    @classmethod
    def get_instance(cls) -> 'AnalyticsService':
        if cls._instance is None:
            cls._instance = AnalyticsService()
        return cls._instance

    def track_event(self, user_id: str, event_name: str, properties: Optional[Dict[str, Any]] = None):
        """Track a discrete event"""
        self.provider.capture(user_id, event_name, properties)

    def identify_user(self, user_id: str, properties: Optional[Dict[str, Any]] = None):
        """Update user properties"""
        self.provider.identify(user_id, properties)


# Global helper for easy access
analytics = AnalyticsService.get_instance()
