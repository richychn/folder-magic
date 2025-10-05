"""
Integration tests for move and rename operations against Google Drive API.

Tests verify real-world behavior of move/rename operations with actual API calls.
"""
import pytest
from backend.app.drive_operations import apply_difflist_to_drive
from backend.models.diff_list import DiffList, Diff


def create_test_file(service, name: str, parent_id: str) -> str:
    """Helper to create a test file in Google Drive."""
    file_metadata = {
        'name': name,
        'parents': [parent_id]
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file['id']


def create_test_folder(service, name: str, parent_id: str) -> str:
    """Helper to create a test folder in Google Drive."""
    folder_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']


@pytest.mark.integration
def test_move_file_integration(drive_service, test_folder):
    """Verify move operation moves file to new parent in Google Drive."""
    # Create source and target folders
    source_id = create_test_folder(drive_service, 'Source', test_folder)
    target_id = create_test_folder(drive_service, 'Target', test_folder)

    # Create test file in source
    file_id = create_test_file(drive_service, 'test.txt', source_id)

    # Create DiffList with move action
    difflist = DiffList(actions=[
        Diff(action_type='move', file_id=file_id, parent_id=target_id)
    ])

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify result
    assert result.successful_operations == 1
    assert result.failed_operations == 0
    assert result.results[0].success is True

    # Verify file is in target folder
    file_meta = drive_service.files().get(fileId=file_id, fields='parents').execute()
    assert target_id in file_meta['parents']
    assert source_id not in file_meta['parents']


@pytest.mark.integration
def test_rename_file_integration(drive_service, test_folder):
    """Verify rename operation changes file name in Google Drive."""
    # Create test file
    file_id = create_test_file(drive_service, 'Original.txt', test_folder)

    # Create DiffList with rename action
    difflist = DiffList(actions=[
        Diff(action_type='rename', file_id=file_id, name='Renamed.txt')
    ])

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify result
    assert result.successful_operations == 1
    assert result.results[0].success is True

    # Verify name changed, file_id unchanged
    file_meta = drive_service.files().get(fileId=file_id, fields='id,name').execute()
    assert file_meta['name'] == 'Renamed.txt'
    assert file_meta['id'] == file_id


@pytest.mark.integration
def test_move_file_not_found_integration(drive_service, test_folder):
    """Verify move with invalid file_id returns error."""
    # Create target folder
    target_id = create_test_folder(drive_service, 'Target', test_folder)

    # Create DiffList with non-existent file_id
    difflist = DiffList(actions=[
        Diff(action_type='move', file_id='nonexistent123', parent_id=target_id)
    ])

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify failure
    assert result.failed_operations == 1
    assert result.results[0].success is False
    assert '404' in str(result.results[0].error_code) or 'not found' in result.results[0].error_message.lower()


@pytest.mark.integration
def test_rename_file_not_found_integration(drive_service, test_folder):
    """Verify rename with invalid file_id returns error."""
    # Create DiffList with non-existent file_id
    difflist = DiffList(actions=[
        Diff(action_type='rename', file_id='nonexistent456', name='NewName.txt')
    ])

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify failure
    assert result.failed_operations == 1
    assert result.results[0].success is False


@pytest.mark.integration
def test_move_and_rename_integration(drive_service, test_folder):
    """Verify combined move and rename operations succeed."""
    # Create source folder and target folder
    source_id = create_test_folder(drive_service, 'Source', test_folder)
    target_id = create_test_folder(drive_service, 'Target', test_folder)

    # Create test file
    file_id = create_test_file(drive_service, 'Original.txt', source_id)

    # Create DiffList with move and rename
    difflist = DiffList(actions=[
        Diff(action_type='move', file_id=file_id, parent_id=target_id),
        Diff(action_type='rename', file_id=file_id, name='NewName.txt')
    ])

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify both succeeded
    assert result.successful_operations == 2

    # Verify file in target with new name
    file_meta = drive_service.files().get(fileId=file_id, fields='name,parents').execute()
    assert file_meta['name'] == 'NewName.txt'
    assert target_id in file_meta['parents']


@pytest.mark.integration
def test_move_partial_success_integration(drive_service, test_folder):
    """Verify partial success when some operations fail."""
    # Create test files and target folder
    file1_id = create_test_file(drive_service, 'file1.txt', test_folder)
    file2_id = create_test_file(drive_service, 'file2.txt', test_folder)
    file3_id = create_test_file(drive_service, 'file3.txt', test_folder)
    target_id = create_test_folder(drive_service, 'Target', test_folder)

    # Create DiffList with valid and invalid operations
    difflist = DiffList(actions=[
        Diff(action_type='move', file_id=file1_id, parent_id=target_id),
        Diff(action_type='move', file_id='invalid_id', parent_id=target_id),
        Diff(action_type='move', file_id=file2_id, parent_id=target_id),
        Diff(action_type='move', file_id=file3_id, parent_id=target_id)
    ])

    # Apply DiffList
    result = apply_difflist_to_drive(drive_service, difflist)

    # Verify partial success
    assert result.successful_operations == 3
    assert result.failed_operations == 1
    assert result.results[1].success is False  # Second operation failed
