import os
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Prompts directory path
PROMPTS_DIR = Path(__file__).parent / "prompts"

def get_prompt(name: str) -> str:
    """
    Load a prompt template from the prompts directory.
    
    Args:
        name: Name of the prompt file (e.g., "birth_data_extractor.system" or "birth_data_extractor.system.txt")
    
    Returns:
        String content of the prompt file
    
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        IOError: If prompt file can't be read
    """
    # Add .txt extension if not present
    if not name.endswith('.txt'):
        name = f"{name}.txt"
    
    prompt_path = PROMPTS_DIR / name
    
    logger.debug(f"Loading prompt from: {prompt_path}")
    
    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully loaded prompt: {name} ({len(content)} characters)")
        return content
    except Exception as e:
        logger.exception(f"Error reading prompt file {prompt_path}: {e}")
        raise IOError(f"Error reading prompt file {prompt_path}: {e}")
