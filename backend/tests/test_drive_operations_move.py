import pytest
from unittest.mock import Mock, MagicMock, patch
from googleapiclient.errors import HttpError
from backend.drive_operations import _create_move_request
from backend.diff_list import Diff


@pytest.fixture
def mock_service():
    """Create a mock Google Drive API service object."""
    service = Mock()
    # Set up the method chaining for files().get().execute()
    service.files.return_value.get.return_value.execute.return_value = {'parents': ['old_parent_id']}
    # Set up the method chaining for files().update().execute()
    service.files.return_value.update.return_value.execute.return_value = {'id': 'file123'}
    return service


def test_create_move_request_success(mock_service):
    """Test successful move operation API request creation."""
    # Configure mock to return single parent
    get_mock = Mock()
    get_mock.execute.return_value = {'parents': ['old_parent_id']}
    mock_service.files.return_value.get.return_value = get_mock

    update_mock = Mock()
    mock_service.files.return_value.update.return_value = update_mock

    # Create Diff object for move operation
    diff = Diff(
        action_type='move',
        file_id='file123',
        parent_id='new_parent_id'
    )

    # Call the function
    request = _create_move_request(mock_service, diff)

    # Verify files().get() was called correctly
    mock_service.files.return_value.get.assert_called_once_with(
        fileId='file123',
        fields='parents'
    )

    # Verify files().update() was called correctly
    mock_service.files.return_value.update.assert_called_once_with(
        fileId='file123',
        addParents='new_parent_id',
        removeParents='old_parent_id',
        fields='id'
    )

    # Verify the request object is returned
    assert request is update_mock


def test_create_move_request_multiple_parents(mock_service):
    """Test move operation with file having multiple current parents."""
    # Configure mock to return multiple parents
    get_mock = Mock()
    get_mock.execute.return_value = {'parents': ['parent1', 'parent2']}
    mock_service.files.return_value.get.return_value = get_mock

    update_mock = Mock()
    mock_service.files.return_value.update.return_value = update_mock

    # Create Diff object for move operation
    diff = Diff(
        action_type='move',
        file_id='file123',
        parent_id='new_parent_id'
    )

    # Call the function
    request = _create_move_request(mock_service, diff)

    # Verify removeParents contains comma-separated list
    mock_service.files.return_value.update.assert_called_once_with(
        fileId='file123',
        addParents='new_parent_id',
        removeParents='parent1,parent2',
        fields='id'
    )

    assert request is update_mock


def test_create_move_request_file_not_found(mock_service):
    """Test move operation when file is not found (404 error)."""
    # Configure mock to raise 404 error on get
    error_response = Mock()
    error_response.status = 404
    error_response.reason = 'Not Found'

    mock_service.files.return_value.get.return_value.execute.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "File not found"}}'
    )

    # Create Diff object for move operation
    diff = Diff(
        action_type='move',
        file_id='nonexistent_file',
        parent_id='new_parent_id'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        _create_move_request(mock_service, diff)

    assert exc_info.value.resp.status == 404


def test_create_move_request_permission_denied(mock_service):
    """Test move operation when permission is denied (403 error)."""
    # Configure mock to raise 403 error
    error_response = Mock()
    error_response.status = 403
    error_response.reason = 'Forbidden'

    mock_service.files.return_value.get.return_value.execute.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "Permission denied"}}'
    )

    # Create Diff object for move operation
    diff = Diff(
        action_type='move',
        file_id='file123',
        parent_id='new_parent_id'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        _create_move_request(mock_service, diff)

    assert exc_info.value.resp.status == 403


def test_create_move_request_parent_not_found(mock_service):
    """Test move operation when target parent folder is not found."""
    # Configure mock to succeed on get but fail on update
    get_mock = Mock()
    get_mock.execute.return_value = {'parents': ['old_parent_id']}
    mock_service.files.return_value.get.return_value = get_mock

    # Note: The error would occur when the request is executed, not when it's created
    # Since _create_move_request only creates the request (doesn't execute it),
    # this test verifies that the request is created successfully
    # The error will be caught during batch execution

    update_mock = Mock()
    mock_service.files.return_value.update.return_value = update_mock

    # Create Diff object for move operation
    diff = Diff(
        action_type='move',
        file_id='file123',
        parent_id='nonexistent_parent'
    )

    # Call the function - it should return the request successfully
    # The error would only occur when the request is executed
    request = _create_move_request(mock_service, diff)
    assert request is update_mock


def test_create_move_request_rate_limit(mock_service):
    """Test move operation when rate limited (429 error)."""
    # Configure mock to raise 429 error
    error_response = Mock()
    error_response.status = 429
    error_response.reason = 'Too Many Requests'

    mock_service.files.return_value.get.return_value.execute.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "Rate limit exceeded"}}'
    )

    # Create Diff object for move operation
    diff = Diff(
        action_type='move',
        file_id='file123',
        parent_id='new_parent_id'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        _create_move_request(mock_service, diff)

    assert exc_info.value.resp.status == 429
