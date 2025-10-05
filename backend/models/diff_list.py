from pydantic import BaseModel
from typing import List, Literal, Optional

class Diff(BaseModel):
    action_type: Literal['move', 'rename', 'create_folder']
    file_id: str
    parent_id: Optional[str] = None # only for move and create_folder
    name: Optional[str] = None # only for rename and create_folder

class DiffList(BaseModel):
    actions: List[Diff]
