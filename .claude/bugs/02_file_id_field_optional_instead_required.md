# Bug Report 02: file_id Field Optional Instead of Required

## Summary
The `OperationResult` model defines `file_id` as optional when it should be required according to the acceptance criteria.

## Issues Found

### Issue 1: file_id Incorrectly Defined as Optional
**Severity**: Medium
**Acceptance Criteria Violated**: Task 001, AC1 - "it includes all required fields: action_index, action_type, file_id, success, error_message, error_code, new_file_id"

**File**: `/Users/richy/code/folder-magic/backend/models/operation_result.py`
**Line**: 9

**Current Code**:
```python
file_id: Optional[str] = None
```

**Expected Code** (per Task 001, Step 4, line 65):
```python
file_id: str
```

**Impact**:
- The model allows creating `OperationResult` objects without a `file_id`
- This deviates from the specification which lists `file_id` as a required field alongside `action_index`, `action_type`, and `success`
- All optional fields should be: `error_message`, `error_code`, and `new_file_id` only

**Test Evidence**:
All tests in `/Users/richy/code/folder-magic/backend/tests/test_operation_result.py` currently pass because they always provide `file_id`, but the model doesn't enforce this requirement.

**Task 001 Specification** (Step 4, lines 62-69):
```
Define OperationResult class:
  - `action_index: int`
  - `action_type: Literal['move', 'rename', 'create_folder']`
  - `file_id: str`  ← Required field, no Optional
  - `success: bool`
  - `error_message: Optional[str] = None`
  - `error_code: Optional[str] = None`
  - `new_file_id: Optional[str] = None`
```

**Recommendation**:
Change line 9 in `/Users/richy/code/folder-magic/backend/models/operation_result.py` from:
```python
file_id: Optional[str] = None
```
to:
```python
file_id: str
```

This ensures the model correctly validates that every operation result has an associated file ID.
