import pytest
from unittest.mock import Mock
from googleapiclient.errors import HttpError
from backend.app.drive_operations import _create_folder_request
from backend.models.diff_list import Diff


@pytest.fixture
def mock_service():
    """Create a mock Google Drive API service object."""
    service = Mock()
    # Set up the method chaining for files().create().execute()
    service.files.return_value.create.return_value.execute.return_value = {'id': 'new_folder_123'}
    return service


def test_create_folder_request_success(mock_service):
    """Test successful create_folder operation API request creation."""
    create_mock = Mock()
    mock_service.files.return_value.create.return_value = create_mock

    # Create Diff object for create_folder operation
    diff = Diff(
        action_type='create_folder',
        file_id='temp_id',
        name='New Folder',
        parent_id='parent_456'
    )

    # Call the function
    request = _create_folder_request(mock_service, diff)

    # Verify files().create() was called correctly
    mock_service.files.return_value.create.assert_called_once_with(
        body={
            'name': 'New Folder',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': ['parent_456']
        },
        fields='id'
    )

    # Verify the request object is returned
    assert request is create_mock


def test_create_folder_request_returns_new_id(mock_service):
    """Test that create_folder operation returns new folder ID."""
    # Configure mock to return specific ID
    mock_service.files.return_value.create.return_value.execute.return_value = {'id': 'new_folder_789'}

    # Create Diff object
    diff = Diff(
        action_type='create_folder',
        file_id='temp_id',
        name='Test Folder',
        parent_id='parent_123'
    )

    # Call the function and execute the request
    request = _create_folder_request(mock_service, diff)
    response = request.execute()

    # Verify the new folder ID is in the response
    assert response['id'] == 'new_folder_789'


def test_create_folder_request_correct_mimetype(mock_service):
    """Test that create_folder uses correct folder mimeType."""
    create_mock = Mock()
    mock_service.files.return_value.create.return_value = create_mock

    # Create Diff object
    diff = Diff(
        action_type='create_folder',
        file_id='temp_id',
        name='My Folder',
        parent_id='parent_abc'
    )

    # Call the function
    request = _create_folder_request(mock_service, diff)

    # Verify mimeType is set to folder type
    call_args = mock_service.files.return_value.create.call_args
    body = call_args.kwargs['body']
    assert body['mimeType'] == 'application/vnd.google-apps.folder'


def test_create_folder_request_parent_not_found(mock_service):
    """Test create_folder operation when parent folder is not found (404 error)."""
    # Configure mock to raise 404 error
    error_response = Mock()
    error_response.status = 404
    error_response.reason = 'Not Found'

    mock_service.files.return_value.create.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "Parent not found"}}'
    )

    # Create Diff object
    diff = Diff(
        action_type='create_folder',
        file_id='temp_id',
        name='New Folder',
        parent_id='nonexistent_parent'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        request = _create_folder_request(mock_service, diff)
        request.execute()

    assert exc_info.value.resp.status == 404


def test_create_folder_request_permission_denied(mock_service):
    """Test create_folder operation when permission is denied (403 error)."""
    # Configure mock to raise 403 error
    error_response = Mock()
    error_response.status = 403
    error_response.reason = 'Forbidden'

    mock_service.files.return_value.create.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "Permission denied"}}'
    )

    # Create Diff object
    diff = Diff(
        action_type='create_folder',
        file_id='temp_id',
        name='New Folder',
        parent_id='parent_123'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        request = _create_folder_request(mock_service, diff)
        request.execute()

    assert exc_info.value.resp.status == 403


def test_create_folder_request_quota_exceeded(mock_service):
    """Test create_folder operation when quota is exceeded (403 error)."""
    # Configure mock to raise 403 error with quota message
    error_response = Mock()
    error_response.status = 403
    error_response.reason = 'Forbidden'

    mock_service.files.return_value.create.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "The user has exceeded their Drive storage quota"}}'
    )

    # Create Diff object
    diff = Diff(
        action_type='create_folder',
        file_id='temp_id',
        name='New Folder',
        parent_id='parent_123'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        request = _create_folder_request(mock_service, diff)
        request.execute()

    assert exc_info.value.resp.status == 403
    assert b'quota' in exc_info.value.content.lower()


def test_create_folder_request_rate_limit(mock_service):
    """Test create_folder operation when rate limited (429 error)."""
    # Configure mock to raise 429 error
    error_response = Mock()
    error_response.status = 429
    error_response.reason = 'Too Many Requests'

    mock_service.files.return_value.create.side_effect = HttpError(
        resp=error_response,
        content=b'{"error": {"message": "Rate limit exceeded"}}'
    )

    # Create Diff object
    diff = Diff(
        action_type='create_folder',
        file_id='temp_id',
        name='New Folder',
        parent_id='parent_123'
    )

    # The function should let the error propagate to the caller
    with pytest.raises(HttpError) as exc_info:
        request = _create_folder_request(mock_service, diff)
        request.execute()

    assert exc_info.value.resp.status == 429


def test_create_folder_request_parents_array(mock_service):
    """Test that parents field is formatted as an array."""
    create_mock = Mock()
    mock_service.files.return_value.create.return_value = create_mock

    # Create Diff object
    diff = Diff(
        action_type='create_folder',
        file_id='temp_id',
        name='New Folder',
        parent_id='specific_parent'
    )

    # Call the function
    request = _create_folder_request(mock_service, diff)

    # Verify parents is an array
    call_args = mock_service.files.return_value.create.call_args
    body = call_args.kwargs['body']
    assert isinstance(body['parents'], list)
    assert body['parents'] == ['specific_parent']
