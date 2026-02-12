"""
User Profile Manager

Maintains a dynamic user profile document that is updated via LLM after each conversation.
This profile captures user preferences, communication style, interests, and context.
Max length: one Telegram message (~4096 characters).
"""

import logging
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.models import User

logger = logging.getLogger(__name__)

# Maximum profile length (Telegram message limit)
MAX_PROFILE_LENGTH = 4000  # Leave some buffer below 4096

class UserProfileManager:
    """Manages dynamic user profiles that evolve through conversation."""
    
    @staticmethod
    def get_user_profile(session: Session, telegram_id: str) -> Optional[str]:
        """
        Retrieve the current user profile document.
        
        Args:
            session: Database session
            telegram_id: User's Telegram ID
            
        Returns:
            User profile document string, or None if not exists
        """
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return None
        
        # Check if user has a profile attribute (we'll add this to User model)
        profile = getattr(user, 'user_profile', None)
        
        if profile:
            logger.debug(f"Retrieved profile for user {telegram_id}: {len(profile)} chars")
        else:
            logger.debug(f"No profile exists for user {telegram_id}")
        
        return profile
    
    @staticmethod
    def update_user_profile(session: Session, telegram_id: str, new_profile: str) -> None:
        """
        Update the user profile document.
        
        Args:
            session: Database session
            telegram_id: User's Telegram ID
            new_profile: New profile document (max MAX_PROFILE_LENGTH chars)
        """
        # Truncate if too long
        if len(new_profile) > MAX_PROFILE_LENGTH:
            logger.warning(f"Profile for {telegram_id} too long ({len(new_profile)} chars), truncating")
            new_profile = new_profile[:MAX_PROFILE_LENGTH]
        
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            logger.error(f"Cannot update profile: user {telegram_id} not found")
            return
        
        # Update profile attribute
        user.user_profile = new_profile
        session.commit()
        
        logger.info(f"Updated profile for user {telegram_id}: {len(new_profile)} chars")
    
    @staticmethod
    def build_profile_prompt(
        current_profile: Optional[str],
        conversation_history: List[Dict[str, str]],
        latest_user_message: str,
        latest_assistant_response: str
    ) -> str:
        """
        Build prompt for LLM to update user profile.
        
        Args:
            current_profile: Current profile document (if exists)
            conversation_history: Recent conversation messages
            latest_user_message: Most recent user message
            latest_assistant_response: Most recent assistant response
            
        Returns:
            Formatted prompt for profile update LLM call
        """
        prompt = """You are maintaining a dynamic user profile for an astrology bot conversation.

Your task: Update the user profile document based on the latest interaction.

The profile should capture:
- User's communication style (brief/detailed, emotional/analytical, direct/exploratory)
- Topics of interest (career, relationships, personal growth, spirituality, etc.)
- Recurring questions or concerns
- Emotional patterns or states
- Preferences in how they like information presented
- Any context that helps provide better responses

IMPORTANT: Keep the profile concise (max 4000 characters).
Format: Natural paragraphs in Russian.
Focus on what's useful for tailoring future responses.

"""
        
        if current_profile:
            prompt += f"""CURRENT PROFILE:
{current_profile}

"""
        else:
            prompt += """CURRENT PROFILE: None (this is the first interaction)

"""
        
        prompt += f"""LATEST INTERACTION:
User: {latest_user_message}
Assistant: {latest_assistant_response[:500]}{'...' if len(latest_assistant_response) > 500 else ''}

"""
        
        if conversation_history and len(conversation_history) > 2:
            prompt += f"""CONVERSATION CONTEXT (last few messages):
"""
            for msg in conversation_history[-4:]:
                role_label = "Пользователь" if msg["role"] == "user" else "Ассистент"
                content_preview = msg["content"][:200]
                if len(msg["content"]) > 200:
                    content_preview += "..."
                prompt += f"{role_label}: {content_preview}\n"
            prompt += "\n"
        
        prompt += """Now provide the UPDATED USER PROFILE in Russian. 
Write naturally, focusing on insights that will help personalize future responses.
If this is the first interaction, create an initial profile based on what you learned.
"""
        
        return prompt


def update_profile_after_interaction(
    session: Session,
    telegram_id: str,
    conversation_history: List[Dict[str, str]],
    latest_user_message: str,
    latest_assistant_response: str
) -> None:
    """
    Update user profile via LLM after each interaction.
    
    This is called after sending a response to the user to update their profile
    based on the latest conversation turn.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        conversation_history: Recent conversation messages
        latest_user_message: Most recent user message
        latest_assistant_response: Most recent assistant response
    """
    from src.llm import call_llm
    
    logger.info(f"Updating profile for user {telegram_id} after interaction")
    
    try:
        # Get current profile
        manager = UserProfileManager()
        current_profile = manager.get_user_profile(session, telegram_id)
        
        # Build prompt for profile update
        prompt = manager.build_profile_prompt(
            current_profile=current_profile,
            conversation_history=conversation_history,
            latest_user_message=latest_user_message,
            latest_assistant_response=latest_assistant_response
        )
        
        # Call LLM to update profile (using parser mode - no personality needed)
        updated_profile = call_llm(
            prompt_type="parser/update_user_profile",
            variables={"prompt": prompt},
            temperature=0.3,  # Lower temperature for consistent profiling
            is_parser=True
        )
        
        # Save updated profile
        manager.update_user_profile(session, telegram_id, updated_profile.strip())
        
        logger.info(f"Profile update completed for user {telegram_id}")
        
    except Exception as e:
        logger.exception(f"Error updating profile for user {telegram_id}: {e}")
        # Don't raise - profile update failure shouldn't break the conversation
