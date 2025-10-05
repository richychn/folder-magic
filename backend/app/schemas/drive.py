from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DriveFileNode(BaseModel):
    """Represents a single file in Google Drive."""

    id: str
    name: str
    parent_id: Optional[str]
    description: Optional[str] = None


class DriveFolderNode(BaseModel):
    """Represents a folder with its immediate children."""

    id: str
    name: str
    parent_id: Optional[str]
    description: Optional[str] = None
    children_folders: List["DriveFolderNode"] = Field(default_factory=list)
    files: List[DriveFileNode] = Field(default_factory=list)


DriveFolderNode.model_rebuild()
