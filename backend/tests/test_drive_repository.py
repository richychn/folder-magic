"""Tests for drive repository module (TDD approach - tests written first)."""

import pytest
from backend.models.drive import DriveFolderNode, DriveFileNode
from backend.models.diff_list import DiffList, Diff
from backend.database.drive_repository import read, initialize, update, delete_user_data


@pytest.mark.asyncio
async def test_read_nonexistent_user():
    """Test reading data for a user that doesn't exist returns None."""
    email = "nonexistent@example.com"
    data = await read(email)
    assert data is None


@pytest.mark.asyncio
async def test_initialize_new_user():
    """Test initializing a new user with current structure."""
    email = "new_user@example.com"

    # Create test structure with nested folder and file
    current_structure = DriveFolderNode(
        id="root",
        name="My Drive",
        parent_id=None,
        children_folders=[
            DriveFolderNode(
                id="folder1",
                name="Test Folder",
                parent_id="root",
                files=[DriveFileNode(id="file1", name="test.txt", parent_id="folder1")]
            )
        ],
        files=[DriveFileNode(id="file2", name="root_file.txt", parent_id="root")]
    )

    # Initialize user
    await initialize(email, current_structure)

    # Read back data
    data = await read(email)

    # Verify structure
    assert data is not None
    assert data["current"] is not None
    assert isinstance(data["current"], DriveFolderNode)
    assert data["current"].id == "root"
    assert data["current"].name == "My Drive"
    assert len(data["current"].children_folders) == 1
    assert len(data["current"].files) == 1
    assert data["proposed"] is None
    assert data["diff"] is None

    # Cleanup
    await delete_user_data(email)


@pytest.mark.asyncio
async def test_initialize_existing_user_resets():
    """Test that initializing an existing user clears proposed and diff."""
    email = "existing_user@example.com"

    # Create initial structure
    initial_structure = DriveFolderNode(
        id="root1",
        name="Initial Drive",
        parent_id=None
    )

    # Initialize first time
    await initialize(email, initial_structure)

    # Verify initial data
    data = await read(email)
    assert data["current"].id == "root1"

    # Create different structure
    different_structure = DriveFolderNode(
        id="root2",
        name="New Drive",
        parent_id=None
    )

    # Reinitialize with different structure
    await initialize(email, different_structure)

    # Read back data
    data = await read(email)

    # Verify new structure and cleared fields
    assert data["current"].id == "root2"
    assert data["current"].name == "New Drive"
    assert data["proposed"] is None
    assert data["diff"] is None

    # Cleanup
    await delete_user_data(email)


@pytest.mark.asyncio
async def test_update_calculates_proposed():
    """Test that update applies diff to calculate proposed structure."""
    email = "update_user@example.com"

    # Create current structure
    current = DriveFolderNode(
        id="root",
        name="My Drive",
        parent_id=None,
        files=[DriveFileNode(id="file1", name="Original.txt", parent_id="root")]
    )

    # Initialize
    await initialize(email, current)

    # Create diff to rename file
    diff_list = DiffList(actions=[
        Diff(action_type="rename", file_id="file1", name="Renamed.txt")
    ])

    # Update with diff
    await update(email, diff_list)

    # Read back data
    data = await read(email)

    # Verify diff was saved
    assert data["diff"] is not None
    assert isinstance(data["diff"], DiffList)
    assert len(data["diff"].actions) == 1
    assert data["diff"].actions[0].action_type == "rename"

    # Verify proposed was calculated
    assert data["proposed"] is not None
    assert isinstance(data["proposed"], DriveFolderNode)
    assert len(data["proposed"].files) == 1
    assert data["proposed"].files[0].name == "Renamed.txt"

    # Cleanup
    await delete_user_data(email)


@pytest.mark.asyncio
async def test_update_with_move_operation():
    """Test update with move operation correctly relocates file."""
    email = "move_test@example.com"

    # Create current structure with two folders
    current = DriveFolderNode(
        id="root",
        name="My Drive",
        parent_id=None,
        children_folders=[
            DriveFolderNode(
                id="folder1",
                name="Folder 1",
                parent_id="root",
                files=[DriveFileNode(id="file1", name="test.txt", parent_id="folder1")]
            ),
            DriveFolderNode(
                id="folder2",
                name="Folder 2",
                parent_id="root"
            )
        ]
    )

    # Initialize
    await initialize(email, current)

    # Create diff to move file from folder1 to folder2
    diff_list = DiffList(actions=[
        Diff(action_type="move", file_id="file1", parent_id="folder2")
    ])

    # Update with diff
    await update(email, diff_list)

    # Read back data
    data = await read(email)

    # Verify file was moved in proposed structure
    assert data["proposed"] is not None
    folder1 = data["proposed"].children_folders[0]
    folder2 = data["proposed"].children_folders[1]

    # File should no longer be in folder1
    assert len(folder1.files) == 0

    # File should now be in folder2
    assert len(folder2.files) == 1
    assert folder2.files[0].id == "file1"
    assert folder2.files[0].parent_id == "folder2"

    # Cleanup
    await delete_user_data(email)


@pytest.mark.asyncio
async def test_update_with_create_folder():
    """Test update with create_folder operation adds new folder."""
    email = "create_test@example.com"

    # Create simple current structure
    current = DriveFolderNode(
        id="root",
        name="My Drive",
        parent_id=None
    )

    # Initialize
    await initialize(email, current)

    # Create diff to add new folder
    diff_list = DiffList(actions=[
        Diff(action_type="create_folder", name="New Folder", parent_id="root")
    ])

    # Update with diff
    await update(email, diff_list)

    # Read back data
    data = await read(email)

    # Verify new folder exists in proposed structure
    assert data["proposed"] is not None
    assert len(data["proposed"].children_folders) == 1
    assert data["proposed"].children_folders[0].name == "New Folder"
    assert data["proposed"].children_folders[0].parent_id == "root"

    # Cleanup
    await delete_user_data(email)


@pytest.mark.asyncio
async def test_nested_folder_serialization():
    """Test that deeply nested folder structures are preserved."""
    email = "nested_test@example.com"

    # Create deeply nested structure (3 levels)
    structure = DriveFolderNode(
        id="root",
        name="Root",
        parent_id=None,
        files=[DriveFileNode(id="file_root", name="root.txt", parent_id="root")],
        children_folders=[
            DriveFolderNode(
                id="level1_a",
                name="Level 1 A",
                parent_id="root",
                files=[DriveFileNode(id="file_1a", name="level1a.txt", parent_id="level1_a")],
                children_folders=[
                    DriveFolderNode(
                        id="level2_a",
                        name="Level 2 A",
                        parent_id="level1_a",
                        files=[DriveFileNode(id="file_2a", name="level2a.txt", parent_id="level2_a")]
                    ),
                    DriveFolderNode(
                        id="level2_b",
                        name="Level 2 B",
                        parent_id="level1_a",
                        files=[DriveFileNode(id="file_2b", name="level2b.txt", parent_id="level2_b")]
                    )
                ]
            ),
            DriveFolderNode(
                id="level1_b",
                name="Level 1 B",
                parent_id="root",
                files=[DriveFileNode(id="file_1b", name="level1b.txt", parent_id="level1_b")]
            )
        ]
    )

    # Initialize with nested structure
    await initialize(email, structure)

    # Read back data
    data = await read(email)

    # Verify all nested levels are preserved
    assert data is not None
    assert data["current"] is not None

    # Check root level
    assert data["current"].id == "root"
    assert len(data["current"].files) == 1
    assert len(data["current"].children_folders) == 2

    # Check level 1
    level1_a = data["current"].children_folders[0]
    level1_b = data["current"].children_folders[1]
    assert level1_a.id == "level1_a"
    assert level1_b.id == "level1_b"
    assert len(level1_a.files) == 1
    assert len(level1_b.files) == 1
    assert len(level1_a.children_folders) == 2

    # Check level 2
    level2_a = level1_a.children_folders[0]
    level2_b = level1_a.children_folders[1]
    assert level2_a.id == "level2_a"
    assert level2_b.id == "level2_b"
    assert len(level2_a.files) == 1
    assert len(level2_b.files) == 1

    # Verify all file counts match
    assert data["current"].files[0].id == "file_root"
    assert level1_a.files[0].id == "file_1a"
    assert level1_b.files[0].id == "file_1b"
    assert level2_a.files[0].id == "file_2a"
    assert level2_b.files[0].id == "file_2b"

    # Cleanup
    await delete_user_data(email)
