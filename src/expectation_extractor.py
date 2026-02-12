"""
User Expectation Extractor

Analyzes conversation history and current message to extract user expectations.
These expectations are injected into LLM prompts to make responses more contextually relevant.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Constants for message length analysis
DETAILED_MESSAGE_THRESHOLD = 200  # Messages longer than this are considered detailed/ready for deep discussion
BRIEF_MESSAGE_THRESHOLD = 50      # Messages shorter than this are considered brief/expecting concise answers

# Constants for question detection
SHORT_MESSAGE_QUESTION_THRESHOLD = 100  # Check question words more aggressively in messages shorter than this
QUESTION_WORD_CHECK_LIMIT = 5          # Number of words to check at message start for question words

# Russian question words for better question detection
RUSSIAN_QUESTION_WORDS = [
    "что", "как", "когда", "почему", "где", "кто", "какой", "какая", "какие",
    "зачем", "откуда", "куда", "сколько", "чей", "чья", "чьё", "чьи"
]

# Topic detection keywords (module-level for performance and maintainability)
CAREER_KEYWORDS = ["работ", "карьер", "професси", "деньг", "финанс", "бизнес"]
RELATIONSHIP_KEYWORDS = ["отношени", "любов", "партнер", "семь", "брак", "друж"]
GROWTH_KEYWORDS = ["развити", "рост", "измени", "потенциал", "цел", "смысл"]
EMOTION_KEYWORDS = ["чувств", "эмоци", "настроени", "переживан", "психолог"]
EMOTIONAL_INDICATORS = ["боюсь", "волнуюсь", "переживаю", "страшно", "тревож", "грустн"]
SPECIFIC_REQUEST_KEYWORDS = ["конкретно", "точно", "именно", "подробн", "детальн"]
TEMPORAL_KEYWORDS = ["сейчас", "сегодня", "завтра", "скоро", "будущ", "прошл"]

# Template for expectation context block
EXPECTATION_CONTEXT_TEMPLATE = """
=== ОЖИДАНИЯ ПОЛЬЗОВАТЕЛЯ ИЗ КОНТЕКСТА ДИАЛОГА ===

{expectations}

ВАЖНО: Учитывай эти ожидания при формировании ответа. Адаптируй тон, глубину и фокус
анализа под потребности пользователя, выявленные из контекста разговора.

============================================
"""


def extract_user_expectations(
    conversation_history: List[Dict[str, str]] = None,
    current_message: str = ""
) -> str:
    """
    Extract user expectations from conversation context and current message.
    
    This function analyzes the conversation to understand:
    - What the user is looking for (e.g., advice, analysis, specific insights)
    - What topics they're interested in (career, relationships, personal growth)
    - Their communication style (direct questions, exploratory, emotional)
    - Context from previous messages
    
    Args:
        conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
        current_message: The user's current message
        
    Returns:
        String description of user expectations to inject into prompts
    """
    if not conversation_history and not current_message:
        return "Пользователь впервые обращается. Ожидает общего астрологического анализа."
    
    expectations_parts = []
    
    # Analyze conversation history if available
    if conversation_history:
        # Extract user messages only
        user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        assistant_messages = [msg["content"] for msg in conversation_history if msg["role"] == "assistant"]
        
        # Detect conversation progression
        conversation_length = len(conversation_history)
        user_message_count = len(user_messages)
        
        logger.debug(f"Analyzing conversation: {conversation_length} total messages, {user_message_count} from user")
        
        # Context: Continuing conversation
        if conversation_length > 2:
            expectations_parts.append(
                f"Продолжение диалога (сообщений в истории: {conversation_length}). "
                "Пользователь ожидает, что ты помнишь контекст предыдущих сообщений."
            )
        
        # Analyze recent user messages to detect patterns
        if user_message_count > 0:
            # Get last few user messages for context
            recent_user_messages = user_messages[-3:] if len(user_messages) >= 3 else user_messages
            
            # Detect question patterns - check for question marks AND question words
            questions_count = sum(1 for msg in recent_user_messages if _is_question(msg))
            if questions_count > 0:
                expectations_parts.append(
                    f"Пользователь задает вопросы (вопросов в недавних сообщениях: {questions_count}). "
                    "Ожидает конкретных ответов и объяснений."
                )
            
            # Detect topics mentioned in conversation
            # Pre-lowercase all messages once for efficiency
            recent_messages_lower = [msg.lower() for msg in recent_user_messages]
            topics_detected = []
            
            # Career/work related - using module-level constant
            if any(any(keyword in msg for keyword in CAREER_KEYWORDS) for msg in recent_messages_lower):
                topics_detected.append("карьера/работа")
            
            # Relationships - using module-level constant
            if any(any(keyword in msg for keyword in RELATIONSHIP_KEYWORDS) for msg in recent_messages_lower):
                topics_detected.append("отношения")
            
            # Personal growth - using module-level constant
            if any(any(keyword in msg for keyword in GROWTH_KEYWORDS) for msg in recent_messages_lower):
                topics_detected.append("личностный рост")
            
            # Emotions/psychology - using module-level constant
            if any(any(keyword in msg for keyword in EMOTION_KEYWORDS) for msg in recent_messages_lower):
                topics_detected.append("эмоции/психология")
            
            if topics_detected:
                expectations_parts.append(
                    f"Обсуждаемые темы: {', '.join(topics_detected)}. "
                    "Пользователь ожидает углубления в эти аспекты."
                )
    
    # Analyze current message
    if current_message:
        current_expectations = []
        
        # Check if it's a question using robust detection
        if _is_question(current_message):
            current_expectations.append("Прямой вопрос - ожидает конкретный ответ")
        
        # Check message length and style using defined constants
        if len(current_message) > DETAILED_MESSAGE_THRESHOLD:
            current_expectations.append("Развернутое сообщение - пользователь готов к детальному диалогу")
        elif len(current_message) < BRIEF_MESSAGE_THRESHOLD:
            current_expectations.append("Короткое сообщение - ожидает лаконичного ответа")
        
        # Detect emotional tone - using module-level constant
        if any(indicator in current_message.lower() for indicator in EMOTIONAL_INDICATORS):
            current_expectations.append("Эмоциональное состояние - ожидает поддержки и эмпатии")
        
        # Detect request for specifics - using module-level constant
        if any(keyword in current_message.lower() for keyword in SPECIFIC_REQUEST_KEYWORDS):
            current_expectations.append("Запрос конкретики - ожидает детальный анализ")
        
        # Detect temporal context - using module-level constant
        if any(keyword in current_message.lower() for keyword in TEMPORAL_KEYWORDS):
            current_expectations.append("Временной контекст - интересует актуальность или прогноз")
        
        if current_expectations:
            expectations_parts.append(
                f"Текущее сообщение: {' | '.join(current_expectations)}"
            )
    
    # Build final expectations string
    if not expectations_parts:
        return "Пользователь начинает новую тему. Ожидает профессионального астрологического анализа."
    
    final_expectations = "\n".join(f"• {part}" for part in expectations_parts)
    
    logger.info(f"Extracted user expectations: {len(expectations_parts)} insights")
    logger.debug(f"Expectations detail:\n{final_expectations}")
    
    return final_expectations


def _is_question(text: str) -> bool:
    """
    Detect if a message is a question using multiple heuristics.
    
    Checks for:
    1. Question mark (?) in text
    2. Russian question words at the start of sentences
    3. Common question patterns
    
    Args:
        text: The message text to analyze
        
    Returns:
        True if the message appears to be a question
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for question mark
    if "?" in text:
        return True
    
    # Check if message starts with a question word
    words = text_lower.split()
    if words and words[0] in RUSSIAN_QUESTION_WORDS:
        return True
    
    # Check for question words anywhere in short messages (likely questions even without ?)
    # Use named constant for threshold
    if len(text) < SHORT_MESSAGE_QUESTION_THRESHOLD:
        # Check first few words - use named constant
        for qword in RUSSIAN_QUESTION_WORDS:
            if qword in words[:QUESTION_WORD_CHECK_LIMIT]:
                return True
    
    return False


def build_expectation_context(
    conversation_history: List[Dict[str, str]] = None,
    current_message: str = ""
) -> str:
    """
    Build a formatted expectation context block for injection into prompts.
    
    This creates a structured section that can be added to any prompt to provide
    context about what the user expects from the response.
    
    Args:
        conversation_history: List of previous messages
        current_message: The user's current message
        
    Returns:
        Formatted string to inject into prompts
    """
    expectations = extract_user_expectations(conversation_history, current_message)
    
    # Use module-level template for consistency and i18n support
    context_block = EXPECTATION_CONTEXT_TEMPLATE.format(expectations=expectations)
    
    return context_block
