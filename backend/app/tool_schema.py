from pydantic import BaseModel, EmailStr, Field

from ..models import DiffList


class ProposeActionsInput(BaseModel):
    """Schema for proposed Drive actions."""

    user_email: EmailStr = Field(..., description="Email of the user performing the actions.")
    actions: DiffList = Field(..., description="List of actions to perform.")


class ProposeActionsBatch(BaseModel):
    """Batch of action proposals for multiple users."""

    proposals: list[ProposeActionsInput] = Field(
        ..., description="List of per-user action proposals to apply in sequence."
    )


class ReadDriveInput(BaseModel):
    """Schema for reading Drive structures for a user."""

    user_email: EmailStr = Field(..., description="Email of the user whose Drive data should be fetched.")
