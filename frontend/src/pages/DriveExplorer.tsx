import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch } from "../api/client";
import PickerButton from "../components/PickerButton";
import DriveList from "../components/DriveList";
import { useAuth } from "../hooks/useAuth";
import type { DriveChildrenResponse } from "../types/drive";

type SelectedFolder = {
  id: string;
  name: string;
};

const DriveExplorerPage = () => {
  const navigate = useNavigate();
  const { user, authenticated, loading: authLoading, refresh } = useAuth();
  const [selectedFolder, setSelectedFolder] = useState<SelectedFolder | null>(null);
  const [result, setResult] = useState<DriveChildrenResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !authenticated) {
      navigate("/", { replace: true });
    }
  }, [authenticated, authLoading, navigate]);

  const loadChildren = useCallback(async (folder: SelectedFolder) => {
    setSelectedFolder(folder);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiFetch<DriveChildrenResponse>(
        `/api/drive/children?folderId=${encodeURIComponent(folder.id)}`
      );
      setResult(data);
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? "Failed to load folder contents");
    } finally {
      setLoading(false);
    }
  }, []);

  const handlePicked = useCallback(
    (folder: SelectedFolder) => {
      void loadChildren(folder);
    },
    [loadChildren]
  );

  const handleLogout = useCallback(async () => {
    try {
      await apiFetch<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
    } finally {
      await refresh();
      navigate("/", { replace: true });
    }
  }, [navigate, refresh]);

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
            <span className="muted">Pick a folder to inspect its immediate children.</span>
          )}
        </div>
        <div className="stack">
          {user?.email ? <span className="tag">{user.email}</span> : null}
          <button type="button" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>

      <section className="card stack">
        <h2>Select a folder</h2>
        <p className="muted">
          The Google Picker opens a Drive prompt. Pick any folder (including Shared drives). We only fetch the
          folder contents on demand—nothing is stored client-side.
        </p>
        <PickerButton onPicked={handlePicked} disabled={loading} />
        {loading ? <span className="muted">Loading folder contents...</span> : null}
        {error ? <span className="notice">{error}</span> : null}
      </section>

      {result ? <DriveList folders={result.folders} files={result.files} /> : null}
    </main>
  );
};

export default DriveExplorerPage;
