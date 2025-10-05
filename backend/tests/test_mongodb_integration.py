"""Integration tests for MongoDB drive repository - end-to-end workflow."""

import pytest
from datetime import datetime, timezone
from backend.database.client import get_database, close_database
from backend.database.drive_repository import read, initialize, update, delete_user_data
from backend.models.drive import DriveFolderNode, DriveFileNode
from backend.models.diff_list import DiffList, Diff


@pytest.mark.asyncio
async def test_database_connection():
    """Test that we can connect to MongoDB database."""
    db = await get_database()
    assert db is not None
    assert db.name == "folder_magic"

    # Verify collection exists
    collection = db["user_drive_data"]
    assert collection is not None


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow: initialize → update → read → verify."""
    email = "integration_test@example.com"

    # Step 1: Test initialize with new user
    current_structure = DriveFolderNode(
        id="root",
        name="My Drive",
        parent_id=None,
        children_folders=[
            DriveFolderNode(
                id="folder1",
                name="Folder 1",
                parent_id="root",
                files=[DriveFileNode(id="file1", name="document.txt", parent_id="folder1")]
            ),
            DriveFolderNode(
                id="folder2",
                name="Folder 2",
                parent_id="root",
                files=[DriveFileNode(id="file2", name="image.jpg", parent_id="folder2")]
            )
        ],
        files=[DriveFileNode(id="file3", name="readme.md", parent_id="root")]
    )

    await initialize(email, current_structure)

    # Verify initialization
    data = await read(email)
    assert data is not None
    assert data["current"] is not None
    assert data["current"].id == "root"
    assert len(data["current"].children_folders) == 2
    assert len(data["current"].files) == 1
    assert data["proposed"] is None
    assert data["diff"] is None

    # Step 2: Test update calculates proposed
    diff_list = DiffList(actions=[
        Diff(action_type="rename", file_id="file1", name="Renamed.txt"),
        Diff(action_type="move", file_id="file2", parent_id="folder1"),
        Diff(action_type="create_folder", name="folder3", parent_id="root")
    ])

    await update(email, diff_list)

    # Verify update
    data = await read(email)
    assert data["diff"] is not None
    assert len(data["diff"].actions) == 3
    assert data["proposed"] is not None

    # Verify rename operation
    folder1 = data["proposed"].children_folders[0]
    renamed_file = [f for f in folder1.files if f.id == "file1"][0]
    assert renamed_file.name == "Renamed.txt"

    # Verify move operation
    moved_file = [f for f in folder1.files if f.id == "file2"][0]
    assert moved_file.parent_id == "folder1"

    # Verify create_folder operation
    assert len(data["proposed"].children_folders) == 3
    new_folder = [f for f in data["proposed"].children_folders if f.name == "folder3"][0]
    assert new_folder.parent_id == "root"

    # Step 3: Test initialize resets existing user
    different_structure = DriveFolderNode(
        id="root2",
        name="New Drive",
        parent_id=None
    )

    await initialize(email, different_structure)

    # Verify reset
    data = await read(email)
    assert data["current"].id == "root2"
    assert data["current"].name == "New Drive"
    assert data["proposed"] is None  # Cleared
    assert data["diff"] is None  # Cleared

    # Step 4: Cleanup
    result = await delete_user_data(email)
    assert result is True

    # Verify deletion
    data = await read(email)
    assert data is None


@pytest.mark.asyncio
async def test_nested_folder_preservation():
    """Test that deeply nested folder structures are preserved correctly."""
    email = "nested_test@example.com"

    # Create deeply nested structure (4 levels)
    nested_structure = DriveFolderNode(
        id="root",
        name="Root",
        parent_id=None,
        files=[DriveFileNode(id="file_root", name="root.txt", parent_id="root")],
        children_folders=[
            DriveFolderNode(
                id="level1",
                name="Level 1",
                parent_id="root",
                files=[DriveFileNode(id="file_level1", name="level1.txt", parent_id="level1")],
                children_folders=[
                    DriveFolderNode(
                        id="level2",
                        name="Level 2",
                        parent_id="level1",
                        files=[DriveFileNode(id="file_level2", name="level2.txt", parent_id="level2")],
                        children_folders=[
                            DriveFolderNode(
                                id="level3",
                                name="Level 3",
                                parent_id="level2",
                                files=[DriveFileNode(id="file_level3", name="level3.txt", parent_id="level3")]
                            )
                        ]
                    )
                ]
            )
        ]
    )

    # Initialize with nested structure
    await initialize(email, nested_structure)

    # Read back data
    data = await read(email)

    # Verify all 4 levels are preserved
    assert data is not None
    assert data["current"] is not None

    # Level 0 (root)
    assert data["current"].id == "root"
    assert len(data["current"].files) == 1
    assert len(data["current"].children_folders) == 1

    # Level 1
    level1 = data["current"].children_folders[0]
    assert level1.id == "level1"
    assert len(level1.files) == 1
    assert len(level1.children_folders) == 1

    # Level 2
    level2 = level1.children_folders[0]
    assert level2.id == "level2"
    assert len(level2.files) == 1
    assert len(level2.children_folders) == 1

    # Level 3
    level3 = level2.children_folders[0]
    assert level3.id == "level3"
    assert len(level3.files) == 1
    assert level3.files[0].id == "file_level3"

    # Verify all file counts match
    assert data["current"].files[0].id == "file_root"
    assert level1.files[0].id == "file_level1"
    assert level2.files[0].id == "file_level2"
    assert level3.files[0].id == "file_level3"

    # Cleanup
    await delete_user_data(email)
