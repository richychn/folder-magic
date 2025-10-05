# tools.py
from .tool_schema import ProposeActionsInput
from ..database.drive_repository import update

async def propose_actions_tool(input_data: dict):
    """Tool that takes LLM-proposed actions, validates, and updates the DB."""
    # Validate the input using Pydantic (raises if invalid)
    parsed = ProposeActionsInput(**input_data)

    # Execute your existing business logic
    await update(parsed.user_email, parsed.actions)

    return {"status": "success"}
