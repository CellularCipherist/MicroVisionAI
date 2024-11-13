from fastapi import APIRouter, Request, Depends, Query, HTTPException, Cookie, Response
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator
import json
import logging

from ..auth import get_current_username
from ..services.atlas_service import generate_improved_prompt, generate_macro_from_prompt

# Create router with prefix
router = APIRouter(
    prefix="/api/v1",
    tags=["chat"]
)
logger = logging.getLogger(__name__)

# Helper function to format EventSource messages as JSON
def format_event(event_type: str, data: dict) -> str:
    return json.dumps({"event": event_type, "data": data})

async def stream_improved_prompt(input: str) -> AsyncGenerator[str, None]:
    try:
        async for chunk in generate_improved_prompt(input):
            yield format_event("improved_prompt_chunk", {"chunk": chunk})
        yield format_event("improved_prompt_complete", {"message": "Prompt improvement complete"})
    except Exception as e:
        logger.error(f"Error in prompt improvement streaming: {str(e)}")
        yield format_event("error", {"error": str(e)})

@router.get("/stream-improve-prompt/")
async def stream_improve_prompt(
    request: Request,
    input: str = Query(..., min_length=1, description="Input for prompt improvement"),
    username: str = Depends(get_current_username)
) -> EventSourceResponse:
    return EventSourceResponse(stream_improved_prompt(input))

async def macro_stream(
    request: Request, input: str, improve_prompt: bool
) -> AsyncGenerator[str, None]:
    try:
        prompt = input
        # Improve prompt if needed
        if improve_prompt:
            async for improved_chunk in generate_improved_prompt(input):
                yield format_event("improved_prompt_chunk", {"chunk": improved_chunk})
            yield format_event("improved_prompt_complete", {"message": "Prompt improvement complete"})
            prompt = improved_chunk  # Use last chunk as final improved prompt

        async for event in generate_macro_from_prompt(prompt):
            if await request.is_disconnected():
                logger.info("Client disconnected. Closing stream.")
                break
            yield format_event(event['event'], event['data'])

    except Exception as e:
        logger.error(f"Error generating macro: {str(e)}")
        yield format_event("error", {"error": str(e)})

from fastapi import Cookie, Response
import secrets

@router.get("/stream-generate-macro")  # Remove trailing slash
async def stream_generate_macro(
    request: Request,
    response: Response,
    input: str = Query(..., min_length=1),
    improve_prompt: bool = Query(False),
    username: str = Depends(get_current_username),
    session: str = Cookie(None)
) -> EventSourceResponse:
    if not session:
        session = secrets.token_urlsafe()
        response.set_cookie(
            key="session",
            value=session,
            httponly=True,
            secure=True,
            samesite="strict"
        )

    return EventSourceResponse(
        macro_stream(request, input, improve_prompt),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
