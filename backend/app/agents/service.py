from __future__ import annotations

import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
_client = AsyncOpenAI(api_key=_settings.openai_api_key)


async def stream_chat_completion(message: str) -> AsyncGenerator[str, None]:
    """Stream assistant output for a single user message."""

    system_prompt = _settings.openai_system_prompt
    logger.info("starting chat stream", extra={"message": message})
    print("[agent] start stream", message)

    try:
        stream = _client.responses.stream(
            model=_settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("failed to create response stream")
        raise

    async with stream as s:
        async for event in s:
            logger.info("agent event", extra={"type": event.type})
            print("[agent] event", event.type)
            if event.type == "response.output_text.delta" and event.delta:
                print("[agent] delta", event.delta)
                yield event.delta
            elif event.type == "response.error":  # pragma: no cover - defensive
                error = event.error or {"message": "Agent response error"}
                logger.error("agent error", extra={"error": error})
                raise RuntimeError(error.get("message", "Agent response error"))

        final = await s.get_final_response()
        logger.info("stream complete", extra={"id": getattr(final, "id", "unknown")})
        print("[agent] stream complete")
