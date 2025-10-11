from __future__ import annotations

import logging
from typing import AsyncGenerator

from agents import Agent, Runner, OpenAIConversationsSession

from ..config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()

assistant_agent = Agent(
    name="Repository Assistant",
    instructions=_settings.openai_system_prompt,
)


async def run_agent(
    session: OpenAIConversationsSession,
    message: str,
) -> AsyncGenerator[str, None]:
    conversation_id = getattr(session, "conversation_id", None)
    logger.info("starting agent run", extra={"conversation_id": conversation_id, "message": message})

    result = await Runner.run(
        assistant_agent,
        message,
        session=session,
    )

    async def stream() -> AsyncGenerator[str, None]:
        output = result.final_output
        if isinstance(output, str):
            yield output
        else:
            yield str(output)

    return stream()
