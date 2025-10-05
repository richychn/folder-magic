# Bug Report 03: Missing google-auth-oauthlib Dependency

## Summary
The `google-auth-oauthlib` package is not included in `pyproject.toml` dependencies, but is required by Task 001 AC3 and is needed by integration tests.

## Issues Found

### Issue 1: google-auth-oauthlib Not in Dependencies
**Severity**: Medium
**Acceptance Criteria Violated**: Task 001, AC3 - "google-auth-oauthlib>=1.0.0 is added to pyproject.toml"

**File**: `/Users/richy/code/folder-magic/pyproject.toml`
**Lines**: 11-23 (dependencies section)

**Current State**:
The dependencies section includes:
- `google-api-python-client>=2.119.0` ✅
- `google-auth>=2.29.0` ✅
- `google-auth-httplib2>=0.2.0` ✅
- `google-auth-oauthlib>=1.0.0` ❌ MISSING

**Expected** (per Task 001, AC3):
```python
dependencies = [
    # ... existing dependencies ...
    "google-auth-oauthlib>=1.0.0",
]
```

**Impact**:
1. Integration tests cannot be collected/run due to import error:
   ```
   ModuleNotFoundError: No module named 'google_auth_oauthlib'
   ```

2. File affected: `/Users/richy/code/folder-magic/backend/tests/integration/conftest.py` (line 12)
   ```python
   from google_auth_oauthlib.flow import InstalledAppFlow
   ```

3. This prevents validation of any integration tests (tasks 015-019), though those are outside the scope of the current validation request (tasks 001-014)

**Task 001 Specification** (AC3, lines 23-29):
```
AC3: Google Drive API Dependencies Added
**Given** the need to interact with Google Drive API
**When** dependencies are installed
**Then** google-api-python-client>=2.0.0 is added to pyproject.toml
**And** google-auth>=2.0.0 is added to pyproject.toml
**And** google-auth-oauthlib>=1.0.0 is added to pyproject.toml  ← MISSING
**And** google-auth-httplib2>=0.1.0 is added to pyproject.toml
**And** all dependencies install successfully with `uv sync`
```

**Recommendation**:
Add `"google-auth-oauthlib>=1.0.0"` to the dependencies array in `pyproject.toml` and run `uv sync` to install it.

**Note**: This dependency is required for OAuth flows with Google services, which will be needed for user authentication in the full application.
