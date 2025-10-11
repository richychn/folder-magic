from __future__ import annotations

from pathlib import Path
from typing import Iterable

_FILE_TYPE_LABELS = {
    "pdf": "PDF document",
    "doc": "Word document",
    "docx": "Word document",
    "xls": "Excel spreadsheet",
    "xlsx": "Excel spreadsheet",
    "csv": "CSV file",
    "ppt": "PowerPoint deck",
    "pptx": "PowerPoint deck",
    "txt": "Text file",
    "md": "Markdown file",
    "json": "JSON file",
}


def _file_type_label(path: Path) -> str:
    suffix = path.suffix.lstrip(".").lower()
    if not suffix:
        return "Unknown type"
    return _FILE_TYPE_LABELS.get(suffix, f"{suffix.upper()} file")


def describe_file(filename: str) -> str:
    """Return a structured description for a file based on its name/extension."""

    path = Path(filename)
    file_type = _file_type_label(path)
    return f"File name: {path.name}; File type: {file_type}."


def describe_folder(folder_name: str, file_names: Iterable[str]) -> str:
    """Build a structured summary for a folder using its name and immediate files."""

    readable_name = Path(folder_name).name
    file_names = list(file_names)
    if file_names:
        formatted = ", ".join(
            f"{Path(name).name} ({_file_type_label(Path(name))})" for name in file_names
        )
    else:
        formatted = "None"

    return f"Folder name: {readable_name}; Files: {formatted}."
