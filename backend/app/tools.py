"""Agent tool implementations for reading and proposing Drive changes."""

from __future__ import annotations

import json
from typing import Any

from .tool_schema import ProposeActionsBatch, ReadDriveInput
from ..database import drive_repository


async def read_drive_tool(params: ReadDriveInput) -> str:
    """Return current/proposed structures and diff list for a user as JSON."""

    data = await drive_repository.read(params.user_email)
    print(f"[read_drive_tool] user_email={params.user_email}")

    if not data:
        payload = {"current": None, "proposed": None, "diff": None}
    else:
        def _dump(value: Any) -> Any:
            if value is None:
                return None
            if hasattr(value, "model_dump"):
                return value.model_dump()
            return value

        payload = {
            "current": _dump(data.get("current")),
            "proposed": _dump(data.get("proposed")),
            "diff": _dump(data.get("diff")),
        }

    return json.dumps(payload)


async def propose_actions_tool(params: ProposeActionsBatch) -> str:
    """Validate proposed actions and update the Drive repository."""

    results = []
    for proposal in params.proposals:
        print(
            "[propose_actions_tool]",
            f"user_email={proposal.user_email}",
            f"actions={proposal.actions.model_dump()}",
        )
        await drive_repository.update(proposal.user_email, proposal.actions)
        results.append({"user_email": proposal.user_email, "status": "success"})

    return json.dumps({"results": results})
