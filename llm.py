import os
import json
import logging
from openai import OpenAI
from prompt_loader import get_prompt

# Configure logging
logger = logging.getLogger(__name__)

# Support DeepSeek and Groq
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # Default to groq

if LLM_PROVIDER == "deepseek":
    logger.info(f"Initializing LLM client with provider: {LLM_PROVIDER}")
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    MODEL = "deepseek-chat"
    logger.info(f"Using model: {MODEL}")
elif LLM_PROVIDER == "groq":
    logger.info(f"Initializing LLM client with provider: {LLM_PROVIDER}")
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
    MODEL = "openai/gpt-oss-20b"
    logger.info(f"Using model: {MODEL}")
else:
    logger.error(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Use 'deepseek' or 'groq'.")


def extract_birth_data(text: str) -> dict:
    """
    Use LLM to extract birth data from natural language text.
    
    Returns:
        dict with keys: dob, time, lat, lng, missing_fields
    """
    logger.debug(f"extract_birth_data called with message length: {len(text)}")
    try:
        system_prompt = get_prompt("birth_data_extractor.system")
        user_prompt = get_prompt("birth_data_extractor.user").format(text=text)
        
        logger.info(f"Making LLM API call for birth data extraction with model: {MODEL}")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1  # Low temperature for consistent extraction
        )
        
        result = response.choices[0].message.content
        logger.debug(f"LLM response: {result}")
        
        # Parse JSON response
        # Clean up response - sometimes LLM might add markdown code blocks
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]  # Remove ```json
        if result.startswith("```"):
            result = result[3:]  # Remove ```
        if result.endswith("```"):
            result = result[:-3]  # Remove ```
        result = result.strip()
        
        birth_data = json.loads(result)
        logger.info(f"Birth data extracted successfully: missing_fields={birth_data.get('missing_fields', [])}")
        
        return birth_data
    except json.JSONDecodeError as e:
        logger.exception(f"Failed to parse JSON from LLM response: {e}")
        logger.error(f"Raw response: {result}")
        raise
    except Exception as e:
        logger.exception(f"Error during birth data extraction: {e}")
        raise


def generate_clarification_question(missing_fields: list, user_message: str) -> str:
    """
    Generate a friendly clarification question for missing birth data fields.
    
    Args:
        missing_fields: List of missing field names
        user_message: The user's previous message
        
    Returns:
        String with clarification question
    """
    logger.debug(f"Generating clarification question for fields: {missing_fields}")
    try:
        system_prompt = get_prompt("clarification_question.system")
        user_prompt = get_prompt("clarification_question.user").format(
            missing_fields=json.dumps(missing_fields),
            user_message=user_message
        )
        
        logger.info(f"Making LLM API call for clarification question with model: {MODEL}")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7  # Moderate temperature for natural language
        )
        
        result = response.choices[0].message.content
        logger.info(f"Clarification question generated, length: {len(result)} characters")
        
        return result.strip()
    except Exception as e:
        logger.exception(f"Error generating clarification question: {e}")
        raise


def interpret_chart(chart_json: dict, question: str = None) -> str:
    """
    Interpret natal chart using LLM.
    
    Args:
        chart_json: The natal chart data
        question: Optional user question for conversational mode
        
    Returns:
        String interpretation
    """
    logger.debug(f"interpret_chart called with {len(chart_json)} chart elements")
    try:
        chart_str = json.dumps(chart_json, indent=2)
        
        system_prompt = get_prompt("astrologer_chat.system")
        
        if question:
            # Conversational mode - user asking about their chart
            user_prompt = get_prompt("astrologer_chat.user").format(
                chart_json=chart_str,
                question=question
            )
        else:
            # Initial reading mode - full chart interpretation
            user_prompt = get_prompt("astrologer_initial_reading.user").format(
                chart_json=chart_str
            )
        
        logger.info(f"Making LLM API call with model: {MODEL}")
        logger.debug(f"Chart data size: {len(chart_str)} characters")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        result = response.choices[0].message.content
        logger.info(f"LLM API call successful, response length: {len(result)} characters")
        logger.debug(f"LLM response preview: {result[:100]}...")
        
        return result
    except Exception as e:
        logger.exception(f"Error during LLM interpretation: {e}")
        raise
