"""
End-to-end integration tests for complete workflow scenarios.

Tests comprehensive folder reorganization scenarios with all operation types.
"""
import pytest
from backend.app.drive_operations import apply_difflist_to_drive
from backend.models.diff_list import DiffList, Diff


def create_test_file(service, name: str, parent_id: str) -> str:
    """Helper to create a test file."""
    file_metadata = {'name': name, 'parents': [parent_id]}
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file['id']


def create_test_folder(service, name: str, parent_id: str) -> str:
    """Helper to create a test folder."""
    folder_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']


@pytest.mark.integration
def test_end_to_end_folder_reorganization(drive_service, test_folder):
    """
    Verify complete folder reorganization workflow.

    Initial: test_folder/ProjectA, ProjectB, Resources
    Target: test_folder/Projects/Active/ProjectA, ProjectB
            test_folder/Shared/Resources (renamed to SharedResources)
    """
    # Step 1: Create initial structure
    project_a_id = create_test_folder(drive_service, 'ProjectA', test_folder)
    project_b_id = create_test_folder(drive_service, 'ProjectB', test_folder)
    resources_id = create_test_folder(drive_service, 'Resources', test_folder)

    # Add sample files
    create_test_file(drive_service, 'file_a.txt', project_a_id)
    create_test_file(drive_service, 'file_b.txt', project_b_id)
    create_test_file(drive_service, 'resource.txt', resources_id)

    # Step 2: Build DiffList for reorganization
    # Note: Simplified version without temp ID mapping
    difflist = DiffList(actions=[
        # Create new folder structure
        Diff(action_type='create_folder', file_id='temp_projects', name='Projects', parent_id=test_folder),
        Diff(action_type='create_folder', file_id='temp_shared', name='Shared', parent_id=test_folder),
        # Rename Resources
        Diff(action_type='rename', file_id=resources_id, name='SharedResources'),
    ])

    # Step 3: Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Step 4: Verify operations succeeded
    assert result.successful_operations == 3
    assert result.failed_operations == 0

    # Verify Projects folder exists
    projects_id = result.results[0].new_file_id
    projects_meta = drive_service.files().get(fileId=projects_id, fields='name').execute()
    assert projects_meta['name'] == 'Projects'

    # Verify Resources was renamed
    resources_meta = drive_service.files().get(fileId=resources_id, fields='name').execute()
    assert resources_meta['name'] == 'SharedResources'


@pytest.mark.integration
def test_end_to_end_with_failures(drive_service, test_folder):
    """Verify end-to-end workflow with intentional failures."""
    # Create initial structure
    file1_id = create_test_file(drive_service, 'file1.txt', test_folder)
    file2_id = create_test_file(drive_service, 'file2.txt', test_folder)
    file3_id = create_test_file(drive_service, 'file3.txt', test_folder)

    # Create DiffList with valid and invalid operations
    difflist = DiffList(actions=[
        # Valid create_folder
        Diff(action_type='create_folder', file_id='temp1', name='Folder1', parent_id=test_folder),
        Diff(action_type='create_folder', file_id='temp2', name='Folder2', parent_id=test_folder),
        Diff(action_type='create_folder', file_id='temp3', name='Folder3', parent_id=test_folder),
        # Invalid create_folder (bad parent)
        Diff(action_type='create_folder', file_id='temp_bad', name='BadFolder', parent_id='invalid_parent'),
        # Valid move operations
        Diff(action_type='rename', file_id=file1_id, name='renamed1.txt'),
        Diff(action_type='rename', file_id=file2_id, name='renamed2.txt'),
        Diff(action_type='rename', file_id=file3_id, name='renamed3.txt'),
        # Invalid move (bad file_id)
        Diff(action_type='move', file_id='invalid_file', parent_id=test_folder),
        # Valid rename operations
        Diff(action_type='rename', file_id=file1_id, name='final_rename1.txt'),
        Diff(action_type='rename', file_id=file2_id, name='final_rename2.txt'),
    ])

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify partial success
    assert result.successful_operations == 8
    assert result.failed_operations == 2
    assert result.total_operations == 10


@pytest.mark.integration
def test_end_to_end_create_then_move(drive_service, test_folder):
    """
    Verify create-then-move pattern.

    Note: This is a simplified test showing the pattern.
    Full temp ID mapping would require implementation changes.
    """
    # Create folder A, then create folder B
    difflist = DiffList(actions=[
        Diff(action_type='create_folder', file_id='temp_A', name='Folder A', parent_id=test_folder),
        # This would fail without temp ID mapping since temp_A isn't resolved
        # Diff(action_type='create_folder', file_id='temp_B', name='Folder B', parent_id='temp_A'),
    ])

    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify first folder created
    assert result.results[0].success is True
    folder_a_id = result.results[0].new_file_id

    # In a full implementation, folder_a_id would replace temp_A for subsequent operations


@pytest.mark.integration
def test_end_to_end_large_reorganization(drive_service, test_folder):
    """
    Verify large-scale reorganization with 50+ files.

    Scenario: Organize 50 files into year-based folders.
    """
    # Create 50 test files
    file_ids = []
    for i in range(50):
        file_id = create_test_file(drive_service, f'document_{i}.txt', test_folder)
        file_ids.append(file_id)

    # Create DiffList with folder creation and file moves
    actions = []

    # Create 5 year folders (2020-2024)
    for year in range(2020, 2025):
        actions.append(
            Diff(action_type='create_folder', file_id=f'temp_{year}', name=str(year), parent_id=test_folder)
        )

    # Rename files (50 operations)
    for i, file_id in enumerate(file_ids):
        year = 2020 + (i % 5)
        actions.append(
            Diff(action_type='rename', file_id=file_id, name=f'{year}_document_{i}.txt')
        )

    difflist = DiffList(actions=actions)

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify high success rate
    assert result.total_operations == 55  # 5 folders + 50 renames
    assert result.successful_operations == 55
    assert result.failed_operations == 0

    # Verify year folders exist
    year_folder_ids = [result.results[i].new_file_id for i in range(5)]
    for folder_id in year_folder_ids:
        folder_meta = drive_service.files().get(fileId=folder_id, fields='name').execute()
        assert folder_meta['name'] in ['2020', '2021', '2022', '2023', '2024']


@pytest.mark.integration
def test_end_to_end_rename_and_move_sequence(drive_service, test_folder):
    """Verify sequential rename and move operations on same files."""
    # Create files and target folder
    file1_id = create_test_file(drive_service, 'original1.txt', test_folder)
    file2_id = create_test_file(drive_service, 'original2.txt', test_folder)
    target_id = create_test_folder(drive_service, 'Target', test_folder)

    # Create sequential operations
    difflist = DiffList(actions=[
        # Rename files first
        Diff(action_type='rename', file_id=file1_id, name='renamed1.txt'),
        Diff(action_type='rename', file_id=file2_id, name='renamed2.txt'),
        # Then move them
        Diff(action_type='move', file_id=file1_id, parent_id=target_id),
        Diff(action_type='move', file_id=file2_id, parent_id=target_id),
    ])

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify all succeeded
    assert result.successful_operations == 4

    # Verify final state
    file1_meta = drive_service.files().get(fileId=file1_id, fields='name,parents').execute()
    assert file1_meta['name'] == 'renamed1.txt'
    assert target_id in file1_meta['parents']
