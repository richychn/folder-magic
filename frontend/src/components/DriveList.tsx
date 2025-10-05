import type { DriveFile, DriveFolder } from "../types/drive";
import { apiFetch } from "../api/client";
import { useState } from "react";

type DriveListProps = {
  folders: DriveFolder[];
  files: DriveFile[];
};

function formatSize(size?: string) {
  if (!size) {
    return "—";
  }
  const value = Number(size);
  if (Number.isNaN(value) || value <= 0) {
    return "—";
  }
  const units = ["B", "KB", "MB", "GB", "TB"];
  const exponent = Math.min(Math.floor(Math.log10(value) / 3), units.length - 1);
  const display = value / 1024 ** exponent;
  return `${display.toFixed(display >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

function formatDate(value?: string) {
  if (!value) {
    return "Unknown";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }
  return date.toLocaleString();
}

const DriveList = ({ folders, files }: DriveListProps) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateFolder = async () => {
    setLoading(true);
    setError(null);

    try {
      await apiFetch("/api/drive/make_change", { method: "POST" });
      // Success - you might want to refresh the folder list or show a success message
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? "Failed to create folder");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-2">
      <section className="card">
        <header className="stack">
          <h2>Subfolders</h2>
          <p className="muted">Immediate child folders inside the selection.</p>
        </header>
        {folders.length === 0 ? (
          <p className="muted">No subfolders found.</p>
        ) : (
          <ul className="list">
            {folders.map((folder) => (
              <li key={folder.id} className="list-item">
                <span>
                  <strong>{folder.name}</strong>
                  {folder.webViewLink ? (
                    <a href={folder.webViewLink} target="_blank" rel="noreferrer">
                      Open in Drive
                    </a>
                  ) : null}
                </span>
                <span className="tag">Folder</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <header className="stack">
          <h2>Files</h2>
          <p className="muted">Files directly inside the selected folder.</p>
        </header>
        {files.length === 0 ? (
          <p className="muted">No files found.</p>
        ) : (
          <ul className="list">
            {files.map((file) => (
              <li key={file.id} className="list-item">
                <span>
                  <strong>{file.name}</strong>
                  <span className="muted">
                    Modified: {formatDate(file.modifiedTime)} · Size: {formatSize(file.size)}
                  </span>
                  {file.webViewLink ? (
                    <a href={file.webViewLink} target="_blank" rel="noreferrer">
                      Open in Drive
                    </a>
                  ) : null}
                </span>
                <span className="tag">File</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <header className="stack">
          <h2>Make Change</h2>
          <button onClick={handleCreateFolder} disabled={loading}>
            {loading ? "Creating..." : "Create New Folder"}
          </button>
          {error ? <span className="notice">{error}</span> : null}
        </header>
      </section>
    </div>
  );
};

export default DriveList;
