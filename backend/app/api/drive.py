from __future__ import annotations

import logging
from typing import Iterable, Optional

import json

from fastapi import APIRouter, HTTPException, Query, Request, status
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...database import drive_repository
from ...models import Diff, DiffList
from ...models.drive import DriveFileNode, DriveFolderNode
from ..drive_operations import apply_difflist_to_drive
from agents import OpenAIConversationsSession

from ..agents.service import run_agent_text
from ..security import ensure_valid_credentials, get_session_store, require_session
from ..utils.drive_descriptions import describe_file, describe_folder

router = APIRouter(prefix="/api/drive", tags=["drive"])
_logger = logging.getLogger(__name__)

_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


def _build_drive_service(credentials):
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _safe_parent_id(item: dict, fallback: str | None = None) -> Optional[str]:
    parents: Iterable[str] | None = item.get("parents")
    if parents:
        return next(iter(parents), fallback)
    return fallback


def _fetch_immediate_files(service, folder_id: str) -> list[DriveFileNode]:
    try:
        response = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="files(id,name,description,mimeType,parents)",
                orderBy="name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
    except HttpError as exc:  # pragma: no cover - network error
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to query Drive API") from exc

    items = response.get("files", [])
    files: list[DriveFileNode] = []
    for item in items:
        if item.get("mimeType") == _FOLDER_MIME_TYPE:
            continue
        name = item.get("name", "")
        files.append(
            DriveFileNode(
                id=item.get("id", ""),
                name=name,
                parent_id=_safe_parent_id(item, folder_id),
                description=describe_file(name),
            )
        )
    return files


def _build_folder_snapshot(service, root_metadata: dict, child_items: list[dict]) -> DriveFolderNode:
    root_id = root_metadata.get("id") or ""

    root_files: list[DriveFileNode] = []
    child_folder_nodes: list[DriveFolderNode] = []

    for item in child_items:
        parent_id = _safe_parent_id(item, root_id)
        if item.get("mimeType") == _FOLDER_MIME_TYPE:
            folder_id = item.get("id", "")
            folder_node = DriveFolderNode(
                id=folder_id,
                name=item.get("name", ""),
                parent_id=parent_id,
                description=None,
            )
            folder_node.files = _fetch_immediate_files(service, folder_id)
            folder_node.description = describe_folder(
                folder_node.name,
                [file.name for file in folder_node.files],
            )
            child_folder_nodes.append(folder_node)
        else:
            name = item.get("name", "")
            root_files.append(
                DriveFileNode(
                    id=item.get("id", ""),
                    name=name,
                    parent_id=parent_id,
                    description=describe_file(name),
                )
            )

    folder_node = DriveFolderNode(
        id=root_id,
        name=root_metadata.get("name", ""),
        parent_id=_safe_parent_id(root_metadata),
        description=None,
        children_folders=child_folder_nodes,
        files=root_files,
    )

    folder_node.description = describe_folder(
        folder_node.name,
        [file.name for file in root_files],
    )

    _logger.info(
        "Built folder snapshot for %s with %d subfolders and %d files",
        folder_node.id,
        len(child_folder_nodes),
        len(root_files),
    )
    print("Folder snapshot:", folder_node.model_dump())

    return folder_node


@router.get("/children")
def list_children(request: Request, folder_id: str = Query(..., alias="folderId")):
    session_id, session = require_session(request)
    store = get_session_store(request)
    credentials = ensure_valid_credentials(session_id, session, store)

    service = _build_drive_service(credentials)
    try:
        root_metadata = (
            service.files()
            .get(fileId=folder_id, fields="id,name,description,parents")
            .execute()
        )
        drive_response = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="files(id,name,description,mimeType,parents,modifiedTime,size,iconLink,webViewLink)",
                orderBy="folder,name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
    except HttpError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to query Drive API") from exc

    items = drive_response.get("files", [])

    folders = [item for item in items if item.get("mimeType") == _FOLDER_MIME_TYPE]
    files = [item for item in items if item.get("mimeType") != _FOLDER_MIME_TYPE]

    snapshot = _build_folder_snapshot(service, root_metadata, items)

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
        "structure": snapshot,
    }


@router.get("/initialize", response_model=DriveFolderNode)
async def initialize_folder(request: Request, folder_id: str = Query(..., alias="folderId")):
    session_id, session = require_session(request)
    store = get_session_store(request)
    credentials = ensure_valid_credentials(session_id, session, store)

    email = session.user.get("email") if session.user else None
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User email unavailable")

    service = _build_drive_service(credentials)
    try:
        root_metadata = (
            service.files()
            .get(fileId=folder_id, fields="id,name,description,parents")
            .execute()
        )
        drive_response = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="files(id,name,description,mimeType,parents)",
                orderBy="folder,name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
    except HttpError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to query Drive API") from exc

    snapshot = _build_folder_snapshot(service, root_metadata, drive_response.get("files", []))

    await drive_repository.initialize(email=email, current=snapshot)

    session.agent_session = OpenAIConversationsSession()

    snapshot_json = json.dumps(snapshot.model_dump(), indent=2)
    intro_message = (
        "You have been provided with a new Google Drive folder snapshot in JSON format. "
        "Acknowledge the data briefly and offer to help.\n"
        f"Snapshot:\n{snapshot_json}"
    )

    try:
        reply_text = await run_agent_text(session.agent_session, intro_message)
        session.pending_agent_messages = [reply_text]
        store.put(session_id, session)
    except Exception as exc:  # pragma: no cover - defensive
        _logger.exception("failed to prime agent with snapshot", exc_info=exc)

    return snapshot


@router.post("/make_change")
def make_change(request: Request):
    session_id, session = require_session(request)
    store = get_session_store(request)
    credentials = ensure_valid_credentials(session_id, session, store)

    service = _build_drive_service(credentials)
    try:
        diff = Diff(action_type="create_folder", name="New Folder", parent_id="root")
        diff_list = DiffList(actions=[diff])
        print("Applying diff list:", diff_list)
        result = apply_difflist_to_drive(service, diff_list)
        print("Change result:", result)
        return {"status": "success", "result": result}
    except HttpError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to make change in Drive") from exc
