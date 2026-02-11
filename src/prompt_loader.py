import os
import logging
import yaml
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Prompts directory path
PROMPTS_DIR = Path(__file__).parent / "prompts"
PERSONALITY_FILE = PROMPTS_DIR / "personality.md"


def _parse_yaml_header(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Parse YAML front matter from markdown content.
    
    Args:
        content: Full markdown content potentially with YAML header
        
    Returns:
        Tuple of (yaml_data_dict or None, content_without_header)
    """
    if not content.startswith('---'):
        return None, content
    
    # Find the closing ---
    lines = content.split('\n')
    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_index = i
            break
    
    if end_index is None:
        # No closing ---, treat as regular content
        return None, content
    
    try:
        yaml_content = '\n'.join(lines[1:end_index])
        yaml_data = yaml.safe_load(yaml_content)
        remaining_content = '\n'.join(lines[end_index + 1:])
        return yaml_data, remaining_content
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse YAML header: {e}")
        return None, content


def _load_personality() -> str:
    """
    Load the global personality layer.
    
    Returns:
        String content of personality.md
    """
    if not PERSONALITY_FILE.exists():
        logger.warning(f"Personality file not found: {PERSONALITY_FILE}")
        return ""
    
    try:
        with open(PERSONALITY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Loaded personality ({len(content)} characters)")
        return content
    except Exception as e:
        logger.exception(f"Error reading personality file: {e}")
        return ""


def load_parser_prompt(name: str) -> str:
    """
    Load a parser prompt from prompts/parser/ directory.
    Parser prompts are used for analyzing user messages, intent detection,
    and data normalization. They do NOT include personality layer.
    
    Args:
        name: Name of the prompt file (e.g., "intent" or "normalize_birth_input")
    
    Returns:
        String content of the prompt file (without personality)
    
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        IOError: If prompt file can't be read
    """
    # Support both .md and without extension
    if not name.endswith('.md'):
        name = f"{name}.md"
    
    prompt_path = PROMPTS_DIR / "parser" / name
    
    logger.debug(f"Loading parser prompt from: {prompt_path}")
    
    if not prompt_path.exists():
        logger.error(f"Parser prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Parser prompt file not found: {prompt_path}")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully loaded parser prompt: {name} ({len(content)} characters)")
        return content
    except Exception as e:
        logger.exception(f"Error reading parser prompt file {prompt_path}: {e}")
        raise IOError(f"Error reading parser prompt file {prompt_path}: {e}")


def load_response_prompt(name: str, include_metadata: bool = False) -> str:
    """
    Load a response prompt from prompts/responses/ directory.
    Response prompts are used for generating responses to users.
    They INCLUDE the personality layer prepended to the prompt.
    
    Args:
        name: Name of the prompt file (e.g., "natal_reading" or "assistant_chat")
        include_metadata: If True, also returns parsed YAML metadata
    
    Returns:
        String content: personality.md + response prompt
        OR tuple (content, metadata) if include_metadata=True
    
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        IOError: If prompt file can't be read
    """
    # Support both .md and without extension
    if not name.endswith('.md'):
        name = f"{name}.md"
    
    prompt_path = PROMPTS_DIR / "responses" / name
    
    logger.debug(f"Loading response prompt from: {prompt_path}")
    
    if not prompt_path.exists():
        logger.error(f"Response prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Response prompt file not found: {prompt_path}")
    
    try:
        # Load response prompt
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse YAML header if present
        metadata, content_without_header = _parse_yaml_header(content)
        
        # Load and prepend personality
        personality = _load_personality()
        
        if personality:
            full_prompt = f"{personality}\n\n{'=' * 60}\n\n{content_without_header}"
        else:
            full_prompt = content_without_header
        
        logger.info(f"Successfully loaded response prompt: {name} ({len(full_prompt)} characters)")
        
        if include_metadata:
            return full_prompt, metadata
        return full_prompt
        
    except Exception as e:
        logger.exception(f"Error reading response prompt file {prompt_path}: {e}")
        raise IOError(f"Error reading response prompt file {prompt_path}: {e}")


# The legacy get_prompt() function was removed per request.
# Backward compatibility helper that loaded .txt prompts has been deleted.
# If other modules relied on get_prompt(), update them to use load_parser_prompt or load_response_prompt instead.
