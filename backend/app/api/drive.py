from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..security import ensure_valid_credentials, get_session_store, require_session
from ..drive_operations import apply_difflist_to_drive
from ...models import Diff, DiffList

router = APIRouter(prefix="/api/drive", tags=["drive"])


@router.get("/children")
def list_children(request: Request, folder_id: str = Query(..., alias="folderId")):
    session_id, session = require_session(request)
    store = get_session_store(request)
    credentials = ensure_valid_credentials(session_id, session, store)

    service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    try:
        drive_response = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="files(id,name,mimeType,modifiedTime,size,iconLink,webViewLink)",
                orderBy="folder,name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
    except HttpError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to query Drive API") from exc

    items = drive_response.get("files", [])

    folders = [item for item in items if item.get("mimeType") == "application/vnd.google-apps.folder"]
    files = [item for item in items if item.get("mimeType") != "application/vnd.google-apps.folder"]

    return {
        "folderId": folder_id,
        "folders": [
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "mimeType": entry.get("mimeType"),
                "iconLink": entry.get("iconLink"),
                "webViewLink": entry.get("webViewLink"),
            }
            for entry in folders
        ],
        "files": [
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "mimeType": entry.get("mimeType"),
                "modifiedTime": entry.get("modifiedTime"),
                "size": entry.get("size"),
                "iconLink": entry.get("iconLink"),
                "webViewLink": entry.get("webViewLink"),
            }
            for entry in files
        ],
    }

@router.post("/make_change")
def make_change(request: Request):
    session_id, session = require_session(request)
    store = get_session_store(request)
    credentials = ensure_valid_credentials(session_id, session, store)

    service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    try:
        # Example change: Create a new folder in the root directory
        diff = Diff(action_type="create_folder", name="New Folder", parent_id="root")
        diff_list = DiffList(actions=[diff])
        print("Applying diff list:", diff_list)
        result = apply_difflist_to_drive(service, diff_list)
        print("Change result:", result)
        return {"status": "success", "result": result}
    except HttpError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to make change in Drive") from exc