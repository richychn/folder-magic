from pydantic import BaseModel
from typing import List, Literal, Optional


class OperationResult(BaseModel):
    """Result of a single DiffList operation."""
    action_index: int
    action_type: Literal['move', 'rename', 'create_folder']
    file_id: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    new_file_id: Optional[str] = None


class DiffListApplicationResult(BaseModel):
    """Result of applying an entire DiffList."""
    total_operations: int
    successful_operations: int
    failed_operations: int
    results: List[OperationResult]
