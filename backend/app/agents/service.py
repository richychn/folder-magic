from __future__ import annotations

import logging
from typing import AsyncGenerator

from pathlib import Path

from agents import Agent, Runner, OpenAIConversationsSession
from agents.tool import function_tool

from ..config import get_settings
from ..tools import propose_actions_tool, read_drive_tool

logger = logging.getLogger(__name__)

_settings = get_settings()

PROMPT_PATH = Path(__file__).resolve().parent / "prompt" / "system_prompt.txt"

with PROMPT_PATH.open("r", encoding="utf-8") as prompt_file:
    SYSTEM_PROMPT = prompt_file.read().strip()

_read_drive_function_tool = function_tool(
    name_override="read_drive_tool",
    description_override="Fetch current, proposed, and diff structures for a user email.",
    use_docstring_info=False,
)(read_drive_tool)

_propose_actions_function_tool = function_tool(
    name_override="propose_actions_tool",
    description_override="Validate and persist Drive change proposals for a user email.",
    use_docstring_info=False,
)(propose_actions_tool)


assistant_agent = Agent(
    name="Repository Assistant",
    instructions=SYSTEM_PROMPT,
    tools=[
        _read_drive_function_tool,
        _propose_actions_function_tool,
    ],
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


async def run_agent_text(
    session: OpenAIConversationsSession,
    message: str,
) -> str:
    conversation_id = getattr(session, "conversation_id", None)
    logger.info("agent run (text)", extra={"conversation_id": conversation_id, "message": message})

    result = await Runner.run(
        assistant_agent,
        message,
        session=session,
    )

    output = result.final_output
    return output if isinstance(output, str) else str(output)
