from pydantic import BaseModel, EmailStr, Field
from ..models import DiffList

class ProposeActionsInput(BaseModel):
    """Schema for the LLM tool input."""
    user_email: EmailStr = Field(..., description="Email of the user performing the actions.")
    actions: DiffList = Field(..., description="List of actions to perform.")