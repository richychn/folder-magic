import pytest
from pydantic import ValidationError
from backend.models import OperationResult, DiffListApplicationResult


def test_operation_result_success_case():
    """Test successful OperationResult creation."""
    result = OperationResult(
        action_index=0,
        action_type='move',
        file_id='123',
        success=True
    )

    assert result.action_index == 0
    assert result.action_type == 'move'
    assert result.file_id == '123'
    assert result.success is True
    assert result.error_message is None
    assert result.error_code is None
    assert result.new_file_id is None


def test_operation_result_failure_case():
    """Test failed OperationResult creation with error details."""
    result = OperationResult(
        action_index=1,
        action_type='rename',
        file_id='456',
        success=False,
        error_message='File not found',
        error_code='404'
    )

    assert result.action_index == 1
    assert result.action_type == 'rename'
    assert result.file_id == '456'
    assert result.success is False
    assert result.error_message == 'File not found'
    assert result.error_code == '404'


def test_operation_result_create_folder_with_new_id():
    """Test create_folder OperationResult with new_file_id."""
    result = OperationResult(
        action_index=2,
        action_type='create_folder',
        file_id='temp_id',
        success=True,
        new_file_id='real_drive_id_789'
    )

    assert result.action_index == 2
    assert result.action_type == 'create_folder'
    assert result.file_id == 'temp_id'
    assert result.success is True
    assert result.new_file_id == 'real_drive_id_789'


def test_operation_result_invalid_action_type():
    """Test that invalid action_type raises ValidationError."""
    with pytest.raises(ValidationError):
        OperationResult(
            action_index=0,
            action_type='delete',  # Invalid action type
            file_id='123',
            success=True
        )


def test_difflist_application_result_creation():
    """Test DiffListApplicationResult with mixed success/failure results."""
    results = [
        OperationResult(
            action_index=0,
            action_type='move',
            file_id='123',
            success=True
        ),
        OperationResult(
            action_index=1,
            action_type='rename',
            file_id='456',
            success=True
        ),
        OperationResult(
            action_index=2,
            action_type='create_folder',
            file_id='789',
            success=False,
            error_message='Permission denied',
            error_code='403'
        )
    ]

    app_result = DiffListApplicationResult(
        total_operations=3,
        successful_operations=2,
        failed_operations=1,
        results=results
    )

    assert app_result.total_operations == 3
    assert app_result.successful_operations == 2
    assert app_result.failed_operations == 1
    assert len(app_result.results) == 3
    assert app_result.results[0].success is True
    assert app_result.results[1].success is True
    assert app_result.results[2].success is False


def test_difflist_application_result_empty():
    """Test DiffListApplicationResult with no operations."""
    app_result = DiffListApplicationResult(
        total_operations=0,
        successful_operations=0,
        failed_operations=0,
        results=[]
    )

    assert app_result.total_operations == 0
    assert app_result.successful_operations == 0
    assert app_result.failed_operations == 0
    assert len(app_result.results) == 0


def test_operation_result_all_action_types():
    """Test that all valid action types create successfully."""
    action_types = ['move', 'rename', 'create_folder']

    for action_type in action_types:
        result = OperationResult(
            action_index=0,
            action_type=action_type,
            file_id='123',
            success=True
        )
        assert result.action_type == action_type
