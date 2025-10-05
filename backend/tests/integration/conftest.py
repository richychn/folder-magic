"""
Integration test fixtures for Google Drive API operations.

Provides authenticated service and test folder management.
"""
from typing import Generator, Optional
import os
import time
import pytest
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# OAuth scope for full Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']

# Path to credentials
CREDENTIALS_FILE = os.path.join(
    os.path.dirname(__file__),
    'credentials.json'
)
TOKEN_FILE = os.path.join(
    os.path.dirname(__file__),
    'token.json'
)


def cleanup_folder(service, folder_id: str) -> None:
    """
    Recursively delete a folder and all its contents.

    Args:
        service: Authenticated Google Drive service
        folder_id: ID of folder to delete

    Handles errors gracefully (e.g., 404 if already deleted).
    """
    try:
        # List all files in the folder
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, mimeType)",
            pageSize=1000
        ).execute()

        items = results.get('files', [])

        # Recursively delete child folders first
        for item in items:
            if item.get('mimeType') == 'application/vnd.google-apps.folder':
                cleanup_folder(service, item['id'])
            else:
                # Delete file
                try:
                    service.files().delete(fileId=item['id']).execute()
                except HttpError as e:
                    # Ignore 404 errors (file already deleted)
                    if e.resp.status != 404:
                        raise

        # Delete the folder itself
        try:
            service.files().delete(fileId=folder_id).execute()
        except HttpError as e:
            # Ignore 404 errors (folder already deleted)
            if e.resp.status != 404:
                raise

    except HttpError as e:
        # Ignore 404 errors (folder already deleted)
        if e.resp.status != 404:
            raise


@pytest.fixture(scope="session")
def drive_service():
    """
    Provide authenticated Google Drive API service.

    Uses credentials.json for OAuth setup and token.json for cached tokens.
    If token is expired, refreshes automatically.

    Returns:
        Authenticated Google Drive service object

    Raises:
        FileNotFoundError: If credentials.json is not found
        ValueError: If authentication fails
    """
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        pytest.skip(
            f"Integration tests require credentials.json at {CREDENTIALS_FILE}. "
            "See backend/tests/integration/README.md for setup instructions."
        )

    creds: Optional[Credentials] = None

    # Load token from file if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            creds.refresh(Request())
        else:
            # Run OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    # Build and return service
    service = build('drive', 'v3', credentials=creds)
    return service


@pytest.fixture
def test_folder(drive_service) -> Generator[str, None, None]:
    """
    Create a unique test folder in Google Drive for test isolation.

    The folder is automatically cleaned up after the test completes,
    including all nested files and folders.

    Args:
        drive_service: Authenticated Google Drive service fixture

    Yields:
        folder_id: ID of the created test folder

    Cleanup:
        Recursively deletes the test folder and all contents
    """
    # Create unique folder name with timestamp
    timestamp = int(time.time() * 1000)
    folder_name = f"folder-magic-test-{timestamp}"

    # Create folder in Google Drive
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    folder = drive_service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    folder_id = folder.get('id')

    # Yield folder_id to test
    yield folder_id

    # Cleanup after test
    cleanup_folder(drive_service, folder_id)
