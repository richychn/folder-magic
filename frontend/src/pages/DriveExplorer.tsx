import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch } from "../api/client";
import PickerButton from "../components/PickerButton";
import { useAuth } from "../hooks/useAuth";
import type { DriveFolderNode } from "../types/drive";

type SelectedFolder = {
  id: string;
  name: string;
};

const DriveExplorerPage = () => {
  const navigate = useNavigate();
  const { user, authenticated, loading: authLoading, refresh } = useAuth();
  const [selectedFolder, setSelectedFolder] = useState<SelectedFolder | null>(null);
  const [snapshot, setSnapshot] = useState<DriveFolderNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !authenticated) {
      navigate("/", { replace: true });
    }
  }, [authenticated, authLoading, navigate]);

  const initializeFolder = useCallback(async (folder: SelectedFolder) => {
    setSelectedFolder(folder);
    setLoading(true);
    setError(null);
    setSnapshot(null);

    try {
      const data = await apiFetch<DriveFolderNode>(
        `/api/drive/initialize?folderId=${encodeURIComponent(folder.id)}`
      );
      setSnapshot(data);
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? "Failed to build folder snapshot");
    } finally {
      setLoading(false);
    }
  }, []);

  const handlePicked = useCallback(
    (folder: SelectedFolder) => {
      void initializeFolder(folder);
    },
    [initializeFolder]
  );

  const handleLogout = useCallback(async () => {
    try {
      await apiFetch<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
    } finally {
      await refresh();
      navigate("/", { replace: true });
    }
  }, [navigate, refresh]);

  const statistics = useMemo(() => {
    if (!snapshot) {
      return null;
    }
    const childFolders = snapshot.children_folders.length;
    const rootFiles = snapshot.files.length;
    const childFiles = snapshot.children_folders.reduce(
      (count, folder) => count + folder.files.length,
      0
    );
    return { childFolders, rootFiles, childFiles };
  }, [snapshot]);

  return (
    <main className="stack">
      <header>
        <div className="stack">
          <h1>Drive Explorer</h1>
          {selectedFolder ? (
            <span className="muted">
              Viewing: {selectedFolder.name} ({selectedFolder.id})
            </span>
          ) : (
            <span className="muted">Pick a folder to generate its two-level snapshot.</span>
          )}
        </div>
        <div className="stack">
          {user?.email ? <span className="tag">{user.email}</span> : null}
          <div className="actions">
            <button type="button" onClick={() => navigate("/agent")}>Chat with Agent</button>
            <button type="button" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      <section className="card stack">
        <h2>Select a folder</h2>
        <p className="muted">
          The Google Picker opens a Drive prompt. Select a folder to build a snapshot that captures the folder and its
          immediate children. We stop at the second level—grandchildren aren&apos;t expanded.
        </p>
        <PickerButton onPicked={handlePicked} disabled={loading} />
        {loading ? <span className="muted">Building snapshot...</span> : null}
        {error ? <span className="notice">{error}</span> : null}
      </section>

      {snapshot ? (
        <section className="card stack">
          <h2>Snapshot Ready</h2>
          {statistics ? (
            <p className="muted">
              Root contains {statistics.childFolders} subfolders, {statistics.rootFiles} files at the root level, and
              {statistics.childFiles} files within those subfolders.
            </p>
          ) : null}
          <details>
            <summary>View JSON snapshot</summary>
            <pre>{JSON.stringify(snapshot, null, 2)}</pre>
          </details>
        </section>
      ) : null}
    </main>
  );
};

export default DriveExplorerPage;
