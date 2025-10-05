from typing import List, Optional, Any
from googleapiclient.http import BatchHttpRequest
from backend.models.diff_list import DiffList, Diff
from backend.models import OperationResult, DiffListApplicationResult


# Constants
FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'
BATCH_SIZE = 100  # Google Drive API batch limit


def apply_difflist_to_drive(
    service,
    difflist: DiffList
) -> DiffListApplicationResult:
    """
    Apply a DiffList to Google Drive.

    Processes actions in batches of up to 100 (Google Drive API limit).
    Batches are executed sequentially to preserve action ordering and dependencies.

    Args:
        service: Authenticated Google Drive API service object (from googleapiclient.discovery.build)
        difflist: DiffList object containing actions to apply

    Returns:
        DiffListApplicationResult with detailed success/failure information

    Raises:
        ValueError: If service is not authenticated or invalid
    """
    # Validate service
    if service is None:
        raise ValueError("service cannot be None")

    # Handle empty DiffList
    if not difflist.actions:
        return DiffListApplicationResult(
            total_operations=0,
            successful_operations=0,
            failed_operations=0,
            results=[]
        )

    # Process in batches of BATCH_SIZE (100)
    all_results = []
    for batch_start in range(0, len(difflist.actions), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(difflist.actions))
        batch_actions = difflist.actions[batch_start:batch_end]
        batch_results = _execute_batch(service, batch_actions, batch_start)
        all_results.extend(batch_results)

    # Aggregate and return results
    return _build_result(all_results)


def _execute_batch(
    service,
    actions: List[Diff],
    start_index: int
) -> List[OperationResult]:
    """
    Execute a batch of up to 100 actions.

    Uses Google Drive API batch requests to execute multiple operations
    efficiently. Each request has a callback that collects results.

    Args:
        service: Authenticated Google Drive API service object
        actions: List of Diff actions to execute (max 100)
        start_index: Starting index in original DiffList for result tracking

    Returns:
        List of OperationResult objects for each action in the batch, ordered by action_index
    """
    # Handle empty batch
    if not actions:
        return []

    # Create results dictionary (indexed by action_index for callback storage)
    results = {}

    # Create batch request
    batch = service.new_batch_http_request()

    # Define callback factory
    def create_callback(action_index: int, action_type: str, file_id: str):
        """Create a callback for a specific action."""
        def callback(request_id, response, exception):
            if exception:
                # Handle error case
                error_code = str(getattr(exception, 'resp', {}).get('status', None)) if hasattr(exception, 'resp') else None
                results[action_index] = OperationResult(
                    action_index=action_index,
                    action_type=action_type,
                    file_id=file_id,
                    success=False,
                    error_message=str(exception),
                    error_code=error_code
                )
            else:
                # Handle success case
                new_file_id = response.get('id') if response else None
                results[action_index] = OperationResult(
                    action_index=action_index,
                    action_type=action_type,
                    file_id=file_id,
                    success=True,
                    new_file_id=new_file_id
                )
        return callback

    # Add each action to the batch
    for i, diff in enumerate(actions):
        action_index = start_index + i

        # Route to appropriate request creation function
        if diff.action_type == 'move':
            request = _create_move_request(service, diff)
        elif diff.action_type == 'rename':
            request = _create_rename_request(service, diff)
        elif diff.action_type == 'create_folder':
            request = _create_folder_request(service, diff)
        else:
            # Unsupported action type - create error result
            results[action_index] = OperationResult(
                action_index=action_index,
                action_type=diff.action_type,
                file_id=diff.file_id,
                success=False,
                error_message=f"Unsupported action type: {diff.action_type}"
            )
            continue

        # Add request to batch with callback
        cb = create_callback(action_index, diff.action_type, diff.file_id)
        batch.add(request, callback=cb)

    # Execute the batch
    batch.execute()

    # Return results in order
    ordered_results = [results[start_index + i] for i in range(len(actions))]
    return ordered_results


def _create_move_request(service, diff: Diff):
    """
    Create API request for move operation.

    Args:
        service: Authenticated Google Drive API service object
        diff: Diff object with action_type='move'

    Returns:
        HttpRequest object for the move operation

    Raises:
        HttpError: For 404 (file/parent not found), 403 (permission denied), 429 (rate limit)
    """
    # Fetch current parents
    current_file = service.files().get(fileId=diff.file_id, fields='parents').execute()
    current_parents = current_file.get('parents', [])

    # Create comma-separated string of current parents for removal
    remove_parents_str = ','.join(current_parents) if current_parents else None

    # Create the update request
    if remove_parents_str:
        request = service.files().update(
            fileId=diff.file_id,
            addParents=diff.parent_id,
            removeParents=remove_parents_str,
            fields='id'
        )
    else:
        # If no current parents, just add the new parent
        request = service.files().update(
            fileId=diff.file_id,
            addParents=diff.parent_id,
            fields='id'
        )

    return request


def _create_rename_request(service, diff: Diff):
    """
    Create API request for rename operation.

    Args:
        service: Authenticated Google Drive API service object
        diff: Diff object with action_type='rename'

    Returns:
        HttpRequest object for the rename operation

    Raises:
        HttpError: For 404 (file not found), 403 (permission denied), 429 (rate limit)
    """
    # Create body with new name
    body = {'name': diff.name}

    # Create the update request
    request = service.files().update(
        fileId=diff.file_id,
        body=body,
        fields='id'
    )

    return request


def _create_folder_request(service, diff: Diff):
    """
    Create API request for create_folder operation.

    Args:
        service: Authenticated Google Drive API service object
        diff: Diff object with action_type='create_folder'

    Returns:
        HttpRequest object for the create_folder operation.
        When executed, response will contain the new folder's ID.

    Raises:
        HttpError: For 404 (parent not found), 403 (permission/quota), 429 (rate limit)
    """
    # Create file metadata for new folder
    file_metadata = {
        'name': diff.name,
        'mimeType': FOLDER_MIMETYPE,
        'parents': [diff.parent_id]
    }

    # Create the request
    request = service.files().create(
        body=file_metadata,
        fields='id'
    )

    return request


def _build_result(results: List[OperationResult]) -> DiffListApplicationResult:
    """
    Build final result object from list of operation results.

    Aggregates individual operation results into a summary with counts
    of total, successful, and failed operations.

    Args:
        results: List of OperationResult objects from all operations

    Returns:
        DiffListApplicationResult with aggregated success/failure counts
    """
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    return DiffListApplicationResult(
        total_operations=total,
        successful_operations=successful,
        failed_operations=failed,
        results=results
    )
