from pydantic import BaseModel, model_validator
from typing import List, Literal, Optional

class Diff(BaseModel):
    action_type: Literal['move', 'rename', 'create_folder']
    file_id: Optional[str] = None # only for move and rename
    parent_id: Optional[str] = None # only for move and create_folder
    name: Optional[str] = None # only for rename and create_folder

    @model_validator(mode="after")
    def validate_dependencies(self):
        """Ensure conditional requirements between fields."""
        if self.action_type == "move":
            if not self.file_id:
                raise ValueError("file_id is required when action_type='move'.")
            if not self.parent_id:
                raise ValueError("parent_id is required when action_type='move'.")
        elif self.action_type == "rename":
            if not self.file_id:
                raise ValueError("file_id is required when action_type='rename'.")
            if not self.name:
                raise ValueError("name is required when action_type='rename'.")
        elif self.action_type == "create_folder":
            if not self.parent_id:
                raise ValueError("parent_id is required when action_type='create_folder'.")
            if not self.name:
                raise ValueError("name is required when action_type='create_folder'.")
        return self

class DiffList(BaseModel):
    actions: List[Diff]
