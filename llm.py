import os
import json
import logging
from openai import OpenAI
from prompt_loader import load_parser_prompt, load_response_prompt

# Configure logging
logger = logging.getLogger(__name__)

# Support DeepSeek and Groq
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # Default to groq

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


def call_llm(prompt_type: str, variables: dict, temperature: float = 0.7, is_parser: bool = None) -> str:
    """
    Universal LLM call function with new prompt architecture.
    
    This function automatically determines if the prompt is a parser or response type,
    loads the appropriate prompt (with or without personality), renders variables,
    and makes the LLM API call.
    
    Args:
        prompt_type: Prompt identifier, e.g., "parser/intent", "responses/natal_reading"
        variables: Dictionary of variables to render in the prompt
        temperature: Temperature for LLM sampling (default 0.7)
        is_parser: Explicitly set if this is a parser prompt (optional, auto-detected from prompt_type)
        
    Returns:
        String response from LLM
        
    Example:
        call_llm(
            prompt_type="responses/natal_reading",
            variables={"chart_json": chart_data},
            temperature=0.7
        )
    """
    logger.debug(f"call_llm invoked with prompt_type={prompt_type}")
    
    try:
        # Auto-detect prompt type if not specified
        if is_parser is None:
            is_parser = prompt_type.startswith("parser/") or "/parser/" in prompt_type
        
        # Load appropriate prompt (parser = no personality, response = with personality)
        if is_parser:
            # Remove "parser/" prefix if present for loading
            prompt_name = prompt_type.replace("parser/", "").replace("/parser/", "")
            prompt_template = load_parser_prompt(prompt_name)
            logger.info(f"Loaded PARSER prompt: {prompt_name} (no personality)")
        else:
            # Remove "responses/" prefix if present for loading
            prompt_name = prompt_type.replace("responses/", "").replace("/responses/", "")
            prompt_template = load_response_prompt(prompt_name)
            logger.info(f"Loaded RESPONSE prompt: {prompt_name} (WITH personality)")
        
        # Render variables into the template
        try:
            rendered_prompt = prompt_template.format(**variables)
        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            # Fallback: use template as-is if variables don't match
            rendered_prompt = prompt_template
            logger.warning("Using prompt template without variable substitution")
        
        logger.debug(f"Rendered prompt length: {len(rendered_prompt)} characters")
        
        # Make LLM API call
        logger.info(f"Making LLM API call with model: {MODEL}, temperature: {temperature}")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": rendered_prompt}
            ],
            temperature=temperature
        )
        
        result = response.choices[0].message.content
        logger.info(f"LLM API call successful, response length: {len(result)} characters")
        logger.debug(f"LLM response preview: {result[:100]}...")
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in call_llm: {e}")
        raise


def extract_birth_data(text: str) -> dict:
    """
    Use LLM to extract birth data from natural language text.
    Uses PARSER prompt (no personality layer).
    
    Returns:
        dict with keys: dob, time, lat, lng, missing_fields
    """
    logger.debug(f"extract_birth_data called with message length: {len(text)}")
    try:
        # Use new prompt architecture
        result = call_llm(
            prompt_type="parser/normalize_birth_input",
            variables={"text": text},
            temperature=0.1,  # Low temperature for consistent extraction
            is_parser=True
        )
        
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
    Uses RESPONSE prompt (with personality layer).
    
    Args:
        missing_fields: List of missing field names
        user_message: The user's previous message
        
    Returns:
        String with clarification question
    """
    logger.debug(f"Generating clarification question for fields: {missing_fields}")
    try:
        # Use new prompt architecture (this is a response, so includes personality)
        result = call_llm(
            prompt_type="responses/clarification",
            variables={
                "missing_fields": json.dumps(missing_fields),
                "user_message": user_message
            },
            temperature=0.7,  # Moderate temperature for natural language
            is_parser=False
        )
        
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
        
        if question:
            # Conversational mode - user asking about their chart
            # Use assistant_chat response prompt (WITH personality)
            result = call_llm(
                prompt_type="responses/assistant_chat",
                variables={
                    "chart_json": chart_str,
                    "question": question
                },
                temperature=0.7,
                is_parser=False
            )
        else:
            # Initial reading mode - full chart interpretation
            # Use natal_reading response prompt (WITH personality)
            result = call_llm(
                prompt_type="responses/natal_reading",
                variables={
                    "chart_json": chart_str
                },
                temperature=0.7,
                is_parser=False
            )
        
        logger.info(f"LLM API call successful, response length: {len(result)} characters")
        logger.debug(f"LLM response preview: {result[:100]}...")
        
        return result
    except Exception as e:
        logger.exception(f"Error during LLM interpretation: {e}")
        raise


def classify_intent(text: str) -> dict:
    """
    Classify user message intent using LLM.
    Uses PARSER prompt (no personality layer).
    
    Args:
        text: User's message text
        
    Returns:
        dict with keys: intent, confidence
        Example: {"intent": "ask_about_chart", "confidence": 0.95}
    """
    logger.debug(f"classify_intent called with message length: {len(text)}")
    result = None  # Initialize to avoid UnboundLocalError
    try:
        # Use new prompt architecture (parser = no personality)
        result = call_llm(
            prompt_type="parser/intent",
            variables={"text": text},
            temperature=0.1,  # Low temperature for consistent classification
            is_parser=True
        )
        
        logger.debug(f"LLM response: {result}")
        
        # Parse JSON response
        # Clean up response - sometimes LLM might add markdown code blocks
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()
        
        intent_data = json.loads(result)
        logger.info(f"Intent classified: {intent_data.get('intent')} with confidence {intent_data.get('confidence')}")
        
        return intent_data
    except json.JSONDecodeError as e:
        logger.exception(f"Failed to parse JSON from LLM response: {e}")
        if result:
            logger.error(f"Raw response: {result}")
        # Return unknown intent on parse error
        return {"intent": "unknown", "confidence": 0.0}
    except Exception as e:
        logger.exception(f"Error during intent classification: {e}")
        # Return unknown intent on any error
        return {"intent": "unknown", "confidence": 0.0}


def generate_assistant_response(context: dict, user_message: str) -> str:
    """
    Generate assistant-style response using personality and astrology knowledge.
    
    Args:
        context: Dict with natal_chart, profile_name, recent_questions, etc.
        user_message: The user's current message
        
    Returns:
        String response from assistant
    """
    logger.debug(f"generate_assistant_response called")
    try:
        # Build context for prompt
        natal_chart = context.get("natal_chart")
        profile_name = context.get("profile_name")
        
        chart_str = json.dumps(natal_chart, indent=2) if natal_chart else "No active profile"
        
        # Use new prompt architecture (response = with personality)
        result = call_llm(
            prompt_type="responses/assistant_chat",
            variables={
                "chart_json": chart_str,
                "question": user_message
            },
            temperature=0.7,  # Moderate temperature for natural conversation
            is_parser=False
        )
        
        logger.info(f"Assistant response generated, length: {len(result)} characters")
        
        return result.strip()
    except Exception as e:
        logger.exception(f"Error generating assistant response: {e}")
        raise


def interpret_transits(natal_chart_json: dict, transits_text: str, user_question: str) -> str:
    """
    Interpret transits in the context of the natal chart.
    Uses RESPONSE prompt (with personality layer).
    
    Args:
        natal_chart_json: User's natal chart data
        transits_text: Formatted transit data (from format_transits_for_llm)
        user_question: User's original question
        
    Returns:
        String interpretation of transits
    """
    logger.debug(f"interpret_transits called")
    try:
        # Format natal chart for prompt
        chart_str = json.dumps(natal_chart_json, indent=2)
        natal_chart_section = f"=== NATAL CHART ===\n{chart_str}"
        
        # Use new prompt architecture (response = with personality)
        result = call_llm(
            prompt_type="responses/transit_reading",
            variables={
                "natal_chart": natal_chart_section,
                "transits": transits_text,
                "question": user_question
            },
            temperature=0.7,
            is_parser=False
        )
        
        logger.info(f"Transit interpretation generated, length: {len(result)} characters")
        
        return result.strip()
    except Exception as e:
        logger.exception(f"Error interpreting transits: {e}")
        raise


def extract_transit_date(text: str) -> dict:
    """
    Use LLM to extract target date for transit calculations from natural language text.
    Uses PARSER prompt (no personality layer).
    
    Args:
        text: User's message text
        
    Returns:
        dict with keys: date (YYYY-MM-DD or null or relative like "tomorrow"), time_specified (bool)
    """
    logger.debug(f"extract_transit_date called with message length: {len(text)}")
    result = None  # Initialize to avoid UnboundLocalError
    try:
        # Use new prompt architecture (parser = no personality)
        result = call_llm(
            prompt_type="parser/detect_transit_date",
            variables={"text": text},
            temperature=0.1,  # Low temperature for consistent extraction
            is_parser=True
        )
        
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
        
        date_data = json.loads(result)
        logger.info(f"Transit date extracted successfully: date={date_data.get('date')}, time_specified={date_data.get('time_specified')}")
        
        return date_data
    except json.JSONDecodeError as e:
        logger.exception(f"Failed to parse JSON from LLM response: {e}")
        if result:
            logger.error(f"Raw response: {result}")
        # Return null date to use current time
        return {"date": None, "time_specified": False}
    except Exception as e:
        logger.exception(f"Error during transit date extraction: {e}")
        # Return null date to use current time
        return {"date": None, "time_specified": False}

