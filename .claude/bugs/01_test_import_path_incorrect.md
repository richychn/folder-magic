# Bug Report 01: Test Import Path Incorrect

## Summary
The test file `test_apply_difflist_to_drive.py` uses incorrect import paths that don't match the actual module structure, causing 5 test failures.

## Test Results
- **Total Tests**: 40
- **Passed**: 35
- **Failed**: 5
- **Error**: 1 (integration tests collection error due to missing `google_auth_oauthlib` dependency)

## Issues Found

### Issue 1: Incorrect Import Path in test_apply_difflist_to_drive.py
**Severity**: Critical
**Acceptance Criteria Violated**: Task 013, AC6 - "All Main Function Tests Pass"

**File**: `/Users/richy/code/folder-magic/backend/tests/test_apply_difflist_to_drive.py`

**Problem**:
Line 3 imports from `backend.app.drive_operations` but lines 29, 60, 107, 149, and 181 patch `backend.drive_operations` (missing the `.app` part).

**Current Code** (Line 3):
```python
from backend.app.drive_operations import apply_difflist_to_drive, _execute_batch
```

**Current Code** (Lines 29, 60, 107, 149, 181):
```python
@patch('backend.drive_operations._execute_batch')
```

**Expected**:
```python
@patch('backend.app.drive_operations._execute_batch')
```

**Failing Tests**:
1. `test_apply_difflist_single_batch` (line 30)
2. `test_apply_difflist_multiple_batches` (line 61)
3. `test_apply_difflist_partial_success` (line 108)
4. `test_apply_difflist_mixed_action_types` (line 150)
5. `test_apply_difflist_result_ordering` (line 182)

**Error Message**:
```
AttributeError: module 'backend' has no attribute 'drive_operations'
```

**Impact**:
All tests that use mocking for `_execute_batch` fail because the patch target path is incorrect. The module exists at `backend.app.drive_operations` not `backend.drive_operations`.

**Acceptance Criteria Check (Task 013)**:
- AC1 (Single Batch): ❌ FAIL - Test exists but fails due to import path
- AC2 (Multi-Batch): ❌ FAIL - Test exists but fails due to import path
- AC3 (Partial Success): ❌ FAIL - Test exists but fails due to import path
- AC4 (Empty DiffList): ✅ PASS - Test passes (no mocking needed)
- AC5 (Mixed Action Types): ❌ FAIL - Test exists but fails due to import path
- AC6 (All Tests Pass): ❌ FAIL - 5 out of 7 tests fail

### Issue 2: Missing Development Dependency
**Severity**: Medium
**File**: Integration test collection

**Problem**:
Integration tests cannot be collected due to missing `google_auth_oauthlib` dependency.

**Error**:
```
ModuleNotFoundError: No module named 'google_auth_oauthlib'
```

**Impact**:
Integration tests in `/Users/richy/code/folder-magic/backend/tests/integration/` cannot run. However, this doesn't affect tasks 001-014 validation as those are unit tests.

**Note**: Task 001 AC3 specifies this dependency should be added to pyproject.toml, but it may need to be installed.

## Recommendations

1. **Fix test import paths** - Update all 5 `@patch` decorators in `test_apply_difflist_to_drive.py` from `backend.drive_operations` to `backend.app.drive_operations`

2. **Install missing dependency** - Run `uv add google-auth-oauthlib` to enable integration test collection

## Overall Status for Tasks 001-014

**Unit Tests Status**: 35/40 passing (87.5%)
- All model tests: ✅ PASS
- All move operation tests: ✅ PASS
- All rename operation tests: ✅ PASS
- All create_folder operation tests: ✅ PASS
- All build_result tests: ✅ PASS
- Apply difflist tests: ❌ 5/7 FAIL (import path issue)

**Acceptance Criteria**: Most criteria are met in implementation, but tests fail due to incorrect import paths preventing validation.
