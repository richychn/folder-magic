"""
Tests to verify integration test fixtures work correctly.

These tests validate that authentication and test folder setup/cleanup
function as expected.
"""
import pytest
from googleapiclient.errors import HttpError


@pytest.mark.integration
def test_drive_service_authenticated(drive_service):
    """
    Verify that drive_service fixture provides authenticated service.

    Tests that the service can make a simple API call to retrieve
    user information.
    """
    # Assert service is not None
    assert drive_service is not None

    # Make simple API call to verify authentication
    about = drive_service.about().get(fields='user').execute()

    # Verify user info is returned
    assert about is not None
    assert 'user' in about
    assert 'emailAddress' in about['user']


@pytest.mark.integration
def test_folder_created_and_cleaned(drive_service, test_folder):
    """
    Verify that test_folder fixture creates and cleans up test folders.

    Tests that:
    1. Test folder is created successfully
    2. Folder exists in Google Drive
    3. Files can be created in the folder
    4. Cleanup removes everything (tested implicitly by fixture teardown)
    """
    # Assert test_folder (folder_id) is not None
    assert test_folder is not None
    assert isinstance(test_folder, str)
    assert len(test_folder) > 0

    # Verify folder exists by getting its metadata
    folder_metadata = drive_service.files().get(
        fileId=test_folder,
        fields='id,name,mimeType'
    ).execute()

    assert folder_metadata['id'] == test_folder
    assert 'folder-magic-test-' in folder_metadata['name']
    assert folder_metadata['mimeType'] == 'application/vnd.google-apps.folder'

    # Create a test file in the folder to verify cleanup works
    file_metadata = {
        'name': 'test-cleanup-file.txt',
        'parents': [test_folder]
    }

    test_file = drive_service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    # Verify file was created
    assert test_file['id'] is not None

    # Create a nested folder to verify recursive cleanup
    nested_folder_metadata = {
        'name': 'nested-folder',
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [test_folder]
    }

    nested_folder = drive_service.files().create(
        body=nested_folder_metadata,
        fields='id'
    ).execute()

    assert nested_folder['id'] is not None

    # Fixture cleanup will verify everything is deleted
    # If cleanup fails, subsequent tests will fail due to leftover folders


@pytest.mark.integration
def test_multiple_test_folders_isolated(drive_service, test_folder):
    """
    Verify that each test gets its own isolated test folder.

    This test creates files to ensure isolation between tests.
    """
    # Create a file in this test's folder
    file_metadata = {
        'name': 'isolation-test-file.txt',
        'parents': [test_folder]
    }

    test_file = drive_service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    # List files in test folder
    results = drive_service.files().list(
        q=f"'{test_folder}' in parents",
        fields="files(id, name)"
    ).execute()

    files = results.get('files', [])

    # Should only have the one file we created
    assert len(files) == 1
    assert files[0]['name'] == 'isolation-test-file.txt'


@pytest.mark.integration
def test_cleanup_handles_already_deleted_items(drive_service, test_folder):
    """
    Verify that cleanup gracefully handles items that are already deleted.

    This tests the error handling in the cleanup_folder function.
    """
    # Create a file
    file_metadata = {
        'name': 'test-file-to-delete.txt',
        'parents': [test_folder]
    }

    test_file = drive_service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    file_id = test_file['id']

    # Manually delete the file before cleanup runs
    drive_service.files().delete(fileId=file_id).execute()

    # Verify file is deleted
    with pytest.raises(HttpError) as exc_info:
        drive_service.files().get(fileId=file_id).execute()

    assert exc_info.value.resp.status == 404

    # Fixture cleanup should handle this gracefully without errors
