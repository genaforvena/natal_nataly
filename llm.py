import os
import json
import logging
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional astrologer.
Interpret only provided chart data.
Avoid clichés.
Write concise psychological analysis."""

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

def interpret_chart(chart_json: dict) -> str:
    # Log only that we're interpreting, not the sensitive chart data
    logger.debug(f"interpret_chart called with {len(chart_json)} chart elements")
    try:
        chart_str = json.dumps(chart_json, indent=2)
        logger.info(f"Making LLM API call with model: {MODEL}")
        # Don't log the actual chart data which contains sensitive birth info
        logger.debug(f"Chart data size: {len(chart_str)} characters")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Interpret this natal chart:\n{chart_str}"}
            ]
        )
        
        result = response.choices[0].message.content
        logger.info(f"LLM API call successful, response length: {len(result)} characters")
        logger.debug(f"LLM response preview: {result[:100]}...")  # Log first 100 chars
        
        return result
    except Exception as e:
        logger.exception(f"Error during LLM interpretation: {e}")
        raise
