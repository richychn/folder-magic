import pytest
from backend.drive_operations import _build_result
from backend.models import OperationResult, DiffListApplicationResult


def test_build_result_all_success():
    """Test building result with all successful operations."""
    results = [
        OperationResult(action_index=i, action_type='move', file_id=f'file{i}', success=True)
        for i in range(5)
    ]

    app_result = _build_result(results)

    assert app_result.total_operations == 5
    assert app_result.successful_operations == 5
    assert app_result.failed_operations == 0
    assert len(app_result.results) == 5


def test_build_result_all_failures():
    """Test building result with all failed operations."""
    results = [
        OperationResult(
            action_index=i,
            action_type='rename',
            file_id=f'file{i}',
            success=False,
            error_message='Error',
            error_code='404'
        )
        for i in range(3)
    ]

    app_result = _build_result(results)

    assert app_result.total_operations == 3
    assert app_result.successful_operations == 0
    assert app_result.failed_operations == 3


def test_build_result_mixed():
    """Test building result with mix of successful and failed operations."""
    results = []

    # 4 successful operations
    for i in range(4):
        results.append(
            OperationResult(action_index=i, action_type='move', file_id=f'file{i}', success=True)
        )

    # 3 failed operations
    for i in range(4, 7):
        results.append(
            OperationResult(
                action_index=i,
                action_type='rename',
                file_id=f'file{i}',
                success=False,
                error_message='Error'
            )
        )

    app_result = _build_result(results)

    assert app_result.total_operations == 7
    assert app_result.successful_operations == 4
    assert app_result.failed_operations == 3


def test_build_result_empty():
    """Test building result with empty results list."""
    results = []

    app_result = _build_result(results)

    assert app_result.total_operations == 0
    assert app_result.successful_operations == 0
    assert app_result.failed_operations == 0
    assert app_result.results == []


def test_build_result_preserves_order():
    """Test that result ordering is preserved."""
    results = [
        OperationResult(action_index=10, action_type='move', file_id='file10', success=True),
        OperationResult(action_index=11, action_type='rename', file_id='file11', success=False, error_message='Error'),
        OperationResult(action_index=12, action_type='create_folder', file_id='file12', success=True),
    ]

    app_result = _build_result(results)

    assert len(app_result.results) == 3
    assert app_result.results[0].action_index == 10
    assert app_result.results[1].action_index == 11
    assert app_result.results[2].action_index == 12
    assert app_result.results[0].action_type == 'move'
    assert app_result.results[1].action_type == 'rename'
    assert app_result.results[2].action_type == 'create_folder'
