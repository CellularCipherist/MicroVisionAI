"""
Atlas service module for the FastAPI application.
Handles AI-powered interactions using the Anthropic API for generating ImageJ macros
with precise formatting and structure requirements.
"""

from typing import AsyncGenerator, Dict, List, Any, Optional
import logging

from anthropic import AsyncAnthropic
from anthropic.types import ContentBlockDeltaEvent
from fastapi import HTTPException

from ..config import load_config
from ..prompts.system_prompts import (
    PROMPT_IMPROVEMENT_SYSTEM,
    PROMPT_IMPROVEMENT_USER,
    MACRO_GENERATION_PROMPT
)

# Initialize core components
config = load_config()
client = AsyncAnthropic(api_key=config.get('api_keys.anthropic'))
logger = logging.getLogger(__name__)

async def generate_improved_prompt(user_input: str) -> AsyncGenerator[str, None]:
    """
    Generate an improved prompt using the Anthropic API with streaming.

    Args:
        user_input (str): The original user input that needs improvement.

    Yields:
        str: Chunks of the improved prompt as they are generated.

    Raises:
        HTTPException: If there's an error in generating the improved prompt.
    """
    try:
        async with client.messages.stream(
            model=config.get('claude.model'),
            max_tokens=config.get('claude.max_tokens'),
            temperature=0.2,
            system=PROMPT_IMPROVEMENT_SYSTEM,
            messages=[{
                "role": "user",
                "content": PROMPT_IMPROVEMENT_USER.format(user_input=user_input)
            }]
        ) as stream:
            async for event in stream.text_stream:
                yield event
    except Exception as e:
        logger.error(f"Error generating improved prompt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate improved prompt")

async def generate_macro_from_prompt(prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate an ImageJ macro script from natural language with streaming.

    Args:
        prompt (str): The user-provided prompt for generating the macro script.

    Yields:
        Dict[str, Any]: Event data containing content updates, section changes, or completion status.

    Raises:
        HTTPException: If an error occurs during the macro generation process.
    """
    user_prompt = (
        f"Generate an ImageJ macro script that accomplishes this task:\n\n"
        f"{prompt}\n\n"
        "Ensure all sections (description, macro script, and explanation) "
        "are properly formatted."
    )

    try:
        current_section = "description"
        section_content = ""

        async with client.messages.stream(
            model=config.get('claude.model'),
            max_tokens=config.get('claude.max_tokens'),
            temperature=0.2,
            system=MACRO_GENERATION_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            yield {
                "event": "section_change",
                "data": {
                    "section": current_section,
                    "content": section_content
                }
            }

            async for event in stream:
                if isinstance(event, ContentBlockDeltaEvent):
                    content_chunk = event.delta.text
                    section_content += content_chunk

                    if handle_section_transition(content_chunk, current_section):
                        for change_event in process_section_change(current_section, section_content):
                            yield change_event
                        current_section = get_next_section(current_section)
                        section_content = ""
                    else:
                        yield {
                            "event": "message",
                            "data": {
                                "content": content_chunk,
                                "section": current_section
                            }
                        }

            if section_content:
                yield {
                    "event": "section_change",
                    "data": {
                        "section": current_section,
                        "content": clean_section_content(current_section, section_content.strip())
                    }
                }

            yield {
                "event": "complete",
                "data": {"message": "Macro generation complete"}
            }

    except Exception as e:
        logger.error(f"Error generating macro: {str(e)}", exc_info=True)
        yield {"event": "error", "data": {"error": str(e)}}
        raise HTTPException(status_code=500, detail="Failed to generate macro script")

def handle_section_transition(content: str, current_section: str) -> bool:
    """
    Determine if the content indicates a transition to a new section.

    Args:
        content (str): The current content chunk.
        current_section (str): The current section being processed.

    Returns:
        bool: True if a section transition is detected, False otherwise.
    """
    if "[DESCRIPTION]" in content:
        return True
    elif "```" in content and current_section == "description":
        return True
    elif "[EXPLANATION]" in content:
        return True
    return False

def get_next_section(current_section: str) -> str:
    """
    Determine the next section based on the current section.

    Args:
        current_section (str): The current section.

    Returns:
        str: The name of the next section.
    """
    sections = ["description", "macro_script", "explanation"]
    current_index = sections.index(current_section)
    return sections[(current_index + 1) % len(sections)]

def process_section_change(current_section: str, content: str) -> List[Dict[str, Any]]:
    """
    Process a section change and return the appropriate event.

    Args:
        current_section (str): The current section that is ending.
        content (str): The content of the section.

    Returns:
        List[Dict[str, Any]]: Event indicating the section change and its content.
    """
    cleaned_content = clean_section_content(current_section, content)
    return [{
        "event": "section_change",
        "data": {
            "section": current_section,
            "content": cleaned_content.strip()
        }
    }]

def clean_section_content(section: str, content: str) -> str:
    """
    Clean the content of a section based on its type.

    Args:
        section (str): The type of section being cleaned.
        content (str): The raw content of the section.

    Returns:
        str: The cleaned content.
    """
    content = content.replace("[DESCRIPTION]", "").replace("[EXPLANATION]", "").strip()

    if section == "macro_script":
        # Remove code block markers but preserve the actual macro code
        content = content.replace("```javascript", "").replace("```", "")

        # Ensure proper macro formatting
        lines = content.split("\n")
        cleaned_lines = [line for line in lines if line.strip()]

        if cleaned_lines:
            # Ensure first line starts with // if it doesn't already
            if not cleaned_lines[0].strip().startswith("//"):
                cleaned_lines.insert(0, "// Generated ImageJ Macro")

        return "\n".join(cleaned_lines)

    return content.strip()
