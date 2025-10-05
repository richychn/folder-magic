"""Repository for managing user drive data in MongoDB."""

import copy
import logging
from datetime import datetime, timezone
from typing import Optional
from backend.models.drive import DriveFolderNode, DriveFileNode
from backend.models.diff_list import DiffList, Diff
from backend.database.client import get_database
from backend.database.exceptions import DatabaseConnectionError


logger = logging.getLogger(__name__)


async def read(email: str) -> Optional[dict]:
    """Read all drive data for a user.

    Args:
        email: User's email address

    Returns:
        Dict with keys 'current', 'proposed', 'diff' (all optional Pydantic models),
        or None if user doesn't exist
    """
    try:
        db = await get_database()
        collection = db["user_drive_data"]
        doc = await collection.find_one({"_id": email})

        if doc is None:
            logger.info(f"No data found for {email}")
            return None

        result = {}
        if "current_structure" in doc:
            result["current"] = DriveFolderNode.model_validate(doc["current_structure"])
        else:
            result["current"] = None

        if "proposed_structure" in doc:
            result["proposed"] = DriveFolderNode.model_validate(doc["proposed_structure"])
        else:
            result["proposed"] = None

        if "diff_list" in doc:
            result["diff"] = DiffList.model_validate(doc["diff_list"])
        else:
            result["diff"] = None

        logger.info(f"Read data for {email}")
        return result

    except Exception as e:
        logger.error(f"Failed to read data for {email}: {e}")
        raise DatabaseConnectionError(f"Failed to read data: {e}")


async def initialize(email: str, current: DriveFolderNode) -> None:
    """Initialize or reset user data with current structure.

    If user exists: sets current, clears proposed and diff.
    If user doesn't exist: creates new document with current.

    Args:
        email: User's email address
        current: Current drive structure
    """
    try:
        db = await get_database()
        collection = db["user_drive_data"]

        current_dict = current.model_dump()

        await collection.update_one(
            {"_id": email},
            {
                "$set": {
                    "current_structure": current_dict,
                    "updated_at": datetime.now(timezone.utc)
                },
                "$unset": {"proposed_structure": "", "diff_list": ""}
            },
            upsert=True
        )

        logger.info(f"Initialized data for {email}")

    except Exception as e:
        logger.error(f"Failed to initialize data for {email}: {e}")
        raise DatabaseConnectionError(f"Failed to initialize data: {e}")


async def update(email: str, diff: DiffList) -> None:
    """Update proposed structure and diff list.

    Reads current structure, applies diff to calculate proposed, saves both.

    Args:
        email: User's email address
        diff: List of diff operations to apply
    """
    try:
        db = await get_database()
        collection = db["user_drive_data"]

        # Read current structure
        doc = await collection.find_one({"_id": email})
        if doc is None or "current_structure" not in doc:
            raise ValueError(f"User {email} must be initialized first")

        current = DriveFolderNode.model_validate(doc["current_structure"])

        # Calculate proposed structure
        proposed = apply_diff_to_structure(current, diff)

        # Convert to dicts
        proposed_dict = proposed.model_dump()
        diff_dict = diff.model_dump()

        # Update document
        await collection.update_one(
            {"_id": email},
            {
                "$set": {
                    "proposed_structure": proposed_dict,
                    "diff_list": diff_dict,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        logger.info(f"Updated proposed and diff for {email}")

    except Exception as e:
        logger.error(f"Failed to update data for {email}: {e}")
        raise DatabaseConnectionError(f"Failed to update data: {e}")


async def delete_user_data(email: str) -> bool:
    """Delete all drive data for a user.

    Args:
        email: User's email address

    Returns:
        True if data was deleted, False otherwise
    """
    try:
        db = await get_database()
        collection = db["user_drive_data"]
        result = await collection.delete_one({"_id": email})

        deleted = result.deleted_count > 0
        logger.info(f"Deleted data for {email}: {deleted}")
        return deleted

    except Exception as e:
        logger.error(f"Failed to delete data for {email}: {e}")
        raise DatabaseConnectionError(f"Failed to delete data: {e}")


def apply_diff_to_structure(current: DriveFolderNode, diff_list: DiffList) -> DriveFolderNode:
    """Apply diff operations to current structure to calculate proposed.

    Args:
        current: Current drive structure
        diff_list: List of diff operations

    Returns:
        Proposed drive structure with diff operations applied
    """
    # Deep copy to avoid modifying original
    proposed = copy.deepcopy(current)

    for diff in diff_list.actions:
        if diff.action_type == "rename":
            _apply_rename(proposed, diff)
        elif diff.action_type == "move":
            _apply_move(proposed, diff)
        elif diff.action_type == "create_folder":
            _apply_create_folder(proposed, diff)

        logger.debug(f"Applied {diff.action_type} operation")

    return proposed


def _apply_rename(folder: DriveFolderNode, diff: Diff) -> None:
    """Apply rename operation to folder structure.

    Args:
        folder: Root folder to search
        diff: Rename diff operation
    """
    # Search for file or folder with file_id
    result = _find_node_by_id(folder, diff.file_id)
    if result is not None:
        node, parent = result
        node.name = diff.name


def _apply_move(folder: DriveFolderNode, diff: Diff) -> None:
    """Apply move operation to folder structure.

    Args:
        folder: Root folder to search
        diff: Move diff operation
    """
    # Find the node to move
    result = _find_node_by_id(folder, diff.file_id)
    if result is None:
        return

    node, old_parent = result

    # Remove from old parent
    if isinstance(node, DriveFileNode):
        old_parent.files = [f for f in old_parent.files if f.id != node.id]
    else:  # DriveFolderNode
        old_parent.children_folders = [f for f in old_parent.children_folders if f.id != node.id]

    # Update parent_id
    node.parent_id = diff.parent_id

    # Find new parent and add node
    new_parent_result = _find_folder_by_id(folder, diff.parent_id)
    if new_parent_result is not None:
        new_parent = new_parent_result
        if isinstance(node, DriveFileNode):
            new_parent.files.append(node)
        else:  # DriveFolderNode
            new_parent.children_folders.append(node)


def _apply_create_folder(folder: DriveFolderNode, diff: Diff) -> None:
    """Apply create_folder operation to folder structure.

    Args:
        folder: Root folder to search
        diff: Create folder diff operation
    """
    # Find parent folder
    parent_result = _find_folder_by_id(folder, diff.parent_id)
    if parent_result is None:
        print("no parent")
        return

    parent = parent_result

    # Generate new folder ID (simple counter-based)
    import uuid
    new_id = f"folder_{uuid.uuid4().hex[:8]}"

    # Create new folder
    new_folder = DriveFolderNode(
        id=new_id,
        name=diff.name,
        parent_id=diff.parent_id
    )

    # Add to parent
    parent.children_folders.append(new_folder)
    print(parent)


def _find_node_by_id(folder: DriveFolderNode, target_id: str) -> Optional[tuple]:
    """Find a file or folder node by ID.

    Args:
        folder: Folder to search
        target_id: ID to find

    Returns:
        Tuple of (node, parent_folder) or None if not found
    """
    # Check if the folder itself is the target
    if folder.id == target_id:
        # Can't return parent for root, return None
        return None

    # Search files in current folder
    for file in folder.files:
        if file.id == target_id:
            return (file, folder)

    # Search child folders in current folder
    for child_folder in folder.children_folders:
        if child_folder.id == target_id:
            return (child_folder, folder)

    # Recursively search in child folders
    for child_folder in folder.children_folders:
        result = _find_node_by_id(child_folder, target_id)
        if result is not None:
            return result

    return None


def _find_folder_by_id(folder: DriveFolderNode, target_id: str) -> Optional[DriveFolderNode]:
    """Find a folder node by ID.

    Args:
        folder: Folder to search
        target_id: ID to find

    Returns:
        Folder node or None if not found
    """
    # Check if this folder is the target
    if folder.id == target_id:
        return folder

    # Recursively search in child folders
    for child_folder in folder.children_folders:
        result = _find_folder_by_id(child_folder, target_id)
        if result is not None:
            return result

    return None
