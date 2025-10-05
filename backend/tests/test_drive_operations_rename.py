import pytest
from unittest.mock import Mock
from googleapiclient.errors import HttpError
from backend.drive_operations import _create_rename_request
from backend.models.diff_list import Diff


@pytest.fixture
def mock_service():
    """Create a mock Google Drive API service object."""
    service = Mock()
    # Set up the method chaining for files().update().execute()
    service.files.return_value.update.return_value.execute.return_value = {'id': 'file123'}
    return service


def test_create_rename_request_success(mock_service):
    """Test successful rename operation API request creation."""
    update_mock = Mock()
    mock_service.files.return_value.update.return_value = update_mock

    # Create Diff object for rename operation
    diff = Diff(
        action_type='rename',
        file_id='file123',
        name='New Name.txt'
    )

    # Call the function
    request = _create_rename_request(mock_service, diff)

    # Verify files().update() was called correctly
    mock_service.files.return_value.update.assert_called_once_with(
        fileId='file123',
        body={'name': 'New Name.txt'},
        fields='id'
    )

    # Verify the request object is returned
    assert request is update_mock


def test_create_rename_request_special_characters(mock_service):
    """Test rename operation with special characters in filename."""
    update_mock = Mock()
    mock_service.files.return_value.update.return_value = update_mock

    # Create Diff object with special characters
    diff = Diff(
        action_type='rename',
        file_id='file123',
        name='File (2023) [final].txt'
    )

    # Call the function
    request = _create_rename_request(mock_service, diff)

    # Verify special characters are passed through unchanged
    mock_service.files.return_value.update.assert_called_once_with(
        fileId='file123',
        body={'name': 'File (2023) [final].txt'},
        fields='id'
    )

    assert request is update_mock


def test_create_rename_request_unicode(mock_service):
    """Test rename operation with Unicode characters in filename."""
    update_mock = Mock()
    mock_service.files.return_value.update.return_value = update_mock

    # Create Diff object with Unicode characters
    diff = Diff(
        action_type='rename',
        file_id='file123',
        name='文件名.txt'
    )

    # Call the function
    request = _create_rename_request(mock_service, diff)

    # Verify Unicode characters are passed through unchanged
    mock_service.files.return_value.update.assert_called_once_with(
        fileId='file123',
        body={'name': '文件名.txt'},
        fields='id'
    )

    assert request is update_mock


def test_create_rename_request_file_not_found(mock_service):
    """Test rename operation when file is not found (404 error)."""
    # Configure mock to raise 404 error
    error_response = Mock()
    error_response.status = 404
    error_response.reason = 'Not Found'

    mock_service.files.return_value.update.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "File not found"}}'
    )

    # Create Diff object for rename operation
    diff = Diff(
        action_type='rename',
        file_id='nonexistent_file',
        name='New Name.txt'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        request = _create_rename_request(mock_service, diff)
        # Execute the request to trigger the error
        request.execute()

    assert exc_info.value.resp.status == 404


def test_create_rename_request_permission_denied(mock_service):
    """Test rename operation when permission is denied (403 error)."""
    # Configure mock to raise 403 error
    error_response = Mock()
    error_response.status = 403
    error_response.reason = 'Forbidden'

    mock_service.files.return_value.update.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "Permission denied"}}'
    )

    # Create Diff object for rename operation
    diff = Diff(
        action_type='rename',
        file_id='file123',
        name='New Name.txt'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        request = _create_rename_request(mock_service, diff)
        # Execute the request to trigger the error
        request.execute()

    assert exc_info.value.resp.status == 403


def test_create_rename_request_rate_limit(mock_service):
    """Test rename operation when rate limited (429 error)."""
    # Configure mock to raise 429 error
    error_response = Mock()
    error_response.status = 429
    error_response.reason = 'Too Many Requests'

    mock_service.files.return_value.update.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "Rate limit exceeded"}}'
    )

    # Create Diff object for rename operation
    diff = Diff(
        action_type='rename',
        file_id='file123',
        name='New Name.txt'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        request = _create_rename_request(mock_service, diff)
        # Execute the request to trigger the error
        request.execute()

    assert exc_info.value.resp.status == 429


def test_create_rename_request_empty_name(mock_service):
    """Test rename operation with empty name (edge case)."""
    update_mock = Mock()
    mock_service.files.return_value.update.return_value = update_mock

    # Create Diff object with empty name
    diff = Diff(
        action_type='rename',
        file_id='file123',
        name=''
    )

    # Call the function - it should create the request
    # Google Drive API will handle validation
    request = _create_rename_request(mock_service, diff)

    # Verify request is created with empty name
    mock_service.files.return_value.update.assert_called_once_with(
        fileId='file123',
        body={'name': ''},
        fields='id'
    )

    assert request is update_mock
