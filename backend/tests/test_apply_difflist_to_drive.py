import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.drive_operations import apply_difflist_to_drive, _execute_batch
from backend.models.diff_list import DiffList, Diff
from backend.models import OperationResult


def test_apply_difflist_empty():
    """Test apply_difflist_to_drive with empty DiffList."""
    mock_service = Mock()
    difflist = DiffList(actions=[])

    result = apply_difflist_to_drive(mock_service, difflist)

    assert result.total_operations == 0
    assert result.successful_operations == 0
    assert result.failed_operations == 0
    assert result.results == []


def test_apply_difflist_none_service():
    """Test that None service raises ValueError."""
    difflist = DiffList(actions=[Diff(action_type='move', file_id='123', parent_id='456')])

    with pytest.raises(ValueError, match="service cannot be None"):
        apply_difflist_to_drive(None, difflist)


@patch('backend.drive_operations._execute_batch')
def test_apply_difflist_single_batch(mock_execute_batch):
    """Test apply_difflist_to_drive with single batch (under 100 actions)."""
    mock_service = Mock()

    # Create 50 actions
    actions = [
        Diff(action_type='move', file_id=f'file{i}', parent_id=f'parent{i}')
        for i in range(50)
    ]
    difflist = DiffList(actions=actions)

    # Mock _execute_batch to return successful results
    mock_results = [
        OperationResult(action_index=i, action_type='move', file_id=f'file{i}', success=True)
        for i in range(50)
    ]
    mock_execute_batch.return_value = mock_results

    result = apply_difflist_to_drive(mock_service, difflist)

    # Verify _execute_batch was called once
    assert mock_execute_batch.call_count == 1
    mock_execute_batch.assert_called_with(mock_service, actions, 0)

    # Verify result
    assert result.total_operations == 50
    assert result.successful_operations == 50
    assert result.failed_operations == 0


@patch('backend.drive_operations._execute_batch')
def test_apply_difflist_multiple_batches(mock_execute_batch):
    """Test apply_difflist_to_drive with multiple batches (over 100 actions)."""
    mock_service = Mock()

    # Create 150 actions
    actions = [
        Diff(action_type='move', file_id=f'file{i}', parent_id=f'parent{i}')
        for i in range(150)
    ]
    difflist = DiffList(actions=actions)

    # Mock _execute_batch to return results based on input
    def execute_batch_side_effect(service, batch_actions, start_index):
        return [
            OperationResult(
                action_index=start_index + i,
                action_type='move',
                file_id=f'file{start_index + i}',
                success=True
            )
            for i in range(len(batch_actions))
        ]

    mock_execute_batch.side_effect = execute_batch_side_effect

    result = apply_difflist_to_drive(mock_service, difflist)

    # Verify _execute_batch was called twice
    assert mock_execute_batch.call_count == 2

    # Verify first batch: 100 actions starting at index 0
    first_call = mock_execute_batch.call_args_list[0]
    assert len(first_call[0][1]) == 100  # batch_actions
    assert first_call[0][2] == 0  # start_index

    # Verify second batch: 50 actions starting at index 100
    second_call = mock_execute_batch.call_args_list[1]
    assert len(second_call[0][1]) == 50  # batch_actions
    assert second_call[0][2] == 100  # start_index

    # Verify result
    assert result.total_operations == 150
    assert result.successful_operations == 150
    assert result.failed_operations == 0


@patch('backend.drive_operations._execute_batch')
def test_apply_difflist_partial_success(mock_execute_batch):
    """Test apply_difflist_to_drive with partial successes."""
    mock_service = Mock()

    # Create 10 actions
    actions = [
        Diff(action_type='move', file_id=f'file{i}', parent_id=f'parent{i}')
        for i in range(10)
    ]
    difflist = DiffList(actions=actions)

    # Mock results: 7 successes, 3 failures
    mock_results = []
    for i in range(10):
        if i in [2, 5, 8]:  # Failures at indices 2, 5, 8
            mock_results.append(
                OperationResult(
                    action_index=i,
                    action_type='move',
                    file_id=f'file{i}',
                    success=False,
                    error_message='Test error',
                    error_code='404'
                )
            )
        else:
            mock_results.append(
                OperationResult(action_index=i, action_type='move', file_id=f'file{i}', success=True)
            )

    mock_execute_batch.return_value = mock_results

    result = apply_difflist_to_drive(mock_service, difflist)

    # Verify result
    assert result.total_operations == 10
    assert result.successful_operations == 7
    assert result.failed_operations == 3
    assert len(result.results) == 10


@patch('backend.drive_operations._execute_batch')
def test_apply_difflist_mixed_action_types(mock_execute_batch):
    """Test apply_difflist_to_drive with mixed action types."""
    mock_service = Mock()

    # Create mixed actions
    actions = [
        Diff(action_type='move', file_id='file1', parent_id='parent1'),
        Diff(action_type='rename', file_id='file2', name='newname.txt'),
        Diff(action_type='create_folder', file_id='temp_id', name='New Folder', parent_id='parent2'),
    ]
    difflist = DiffList(actions=actions)

    # Mock results
    mock_results = [
        OperationResult(action_index=0, action_type='move', file_id='file1', success=True),
        OperationResult(action_index=1, action_type='rename', file_id='file2', success=True),
        OperationResult(action_index=2, action_type='create_folder', file_id='temp_id', success=True, new_file_id='new_id_123'),
    ]
    mock_execute_batch.return_value = mock_results

    result = apply_difflist_to_drive(mock_service, difflist)

    # Verify result
    assert result.total_operations == 3
    assert result.successful_operations == 3
    assert result.results[0].action_type == 'move'
    assert result.results[1].action_type == 'rename'
    assert result.results[2].action_type == 'create_folder'
    assert result.results[2].new_file_id == 'new_id_123'


@patch('backend.drive_operations._execute_batch')
def test_apply_difflist_result_ordering(mock_execute_batch):
    """Test that result ordering is preserved across batches."""
    mock_service = Mock()

    # Create 150 actions
    actions = [
        Diff(action_type='move', file_id=f'file{i}', parent_id=f'parent{i}')
        for i in range(150)
    ]
    difflist = DiffList(actions=actions)

    # Mock _execute_batch to return results with correct indices
    def execute_batch_side_effect(service, batch_actions, start_index):
        return [
            OperationResult(
                action_index=start_index + i,
                action_type='move',
                file_id=f'file{start_index + i}',
                success=True
            )
            for i in range(len(batch_actions))
        ]

    mock_execute_batch.side_effect = execute_batch_side_effect

    result = apply_difflist_to_drive(mock_service, difflist)

    # Verify ordering
    assert result.results[0].action_index == 0
    assert result.results[99].action_index == 99
    assert result.results[100].action_index == 100
    assert result.results[149].action_index == 149
