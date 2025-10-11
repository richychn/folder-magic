import type { DriveFile, DriveFolder } from "../types/drive";

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

  return (
    <div className="stack">
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
    </div>
  );
};

export default DriveList;
