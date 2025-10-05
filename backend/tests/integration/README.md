# Integration Tests for Google Drive API

This directory contains integration tests that interact with the actual Google Drive API. These tests require valid credentials and make real API calls.

## Setup Instructions

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

### 2. Enable Google Drive API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click "Enable"

### 3. Create OAuth 2.0 Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select application type: "Desktop app"
4. Name it (e.g., "folder-magic-integration-tests")
5. Click "Create"
6. Download the credentials JSON file

### 4. Save Credentials

1. Save the downloaded file as `credentials.json` in this directory:
   ```
   backend/tests/integration/credentials.json
   ```
2. **Important**: This file is gitignored and should never be committed

### 5. Generate Token

The first time you run integration tests, you'll need to authenticate:

```bash
# Run a simple integration test to trigger auth flow
uv run pytest backend/tests/integration/test_fixtures.py::test_drive_service_authenticated -v -m integration
```

This will:
- Open a browser window for Google OAuth consent
- Ask you to sign in and grant permissions
- Save the token to `backend/tests/integration/token.json` (gitignored)

### 6. Credentials File Format

The `credentials.json` file should have this structure:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

See `credentials.json.example` for a template.

## Running Integration Tests

### Run all integration tests:
```bash
uv run pytest backend/tests/integration/ -v -m integration
```

### Run a specific integration test file:
```bash
uv run pytest backend/tests/integration/test_move_rename_operations.py -v -m integration
```

### Run a specific test:
```bash
uv run pytest backend/tests/integration/test_fixtures.py::test_drive_service_authenticated -v -m integration
```

## Test Environment

- **Test Folder**: Each test creates a uniquely named test folder in your Google Drive
- **Cleanup**: Test folders and their contents are automatically deleted after each test
- **Isolation**: Tests do not interfere with your existing Google Drive files

## Security Notes

1. **Never commit credentials**: `credentials.json` and `token.json` are gitignored
2. **Use test account**: Consider using a dedicated Google account for testing
3. **OAuth scope**: Tests require full Drive access (`https://www.googleapis.com/auth/drive`)
4. **Revoke access**: You can revoke access at https://myaccount.google.com/permissions

## Troubleshooting

### "credentials.json not found"
- Make sure you've placed the credentials file in `backend/tests/integration/credentials.json`
- Check that the file is not empty and has valid JSON

### "token.json not found" or authentication errors
- Delete `token.json` if it exists
- Run the tests again to trigger a new authentication flow

### "API has not been used in project"
- Make sure you've enabled the Google Drive API in your Google Cloud project
- Wait a few minutes for the API to be fully enabled

### "Rate limit exceeded" (429 errors)
- Reduce the number of concurrent tests
- Add delays between test runs
- Consider using a different test account

## Environment Variables (Alternative to credentials.json)

Instead of using a credentials file, you can set environment variables:

```bash
export GOOGLE_DRIVE_CLIENT_ID="your_client_id"
export GOOGLE_DRIVE_CLIENT_SECRET="your_client_secret"
export GOOGLE_DRIVE_REFRESH_TOKEN="your_refresh_token"
```

The test fixtures will check for these variables if `credentials.json` is not found.
