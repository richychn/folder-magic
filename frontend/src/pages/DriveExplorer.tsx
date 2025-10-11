import { useCallback, useEffect, useMemo, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch } from "../api/client";
import AgentChatEmbed from "../components/AgentChatEmbed";
import DriveList from "../components/DriveList";
import PickerButton from "../components/PickerButton";
import { useAuth } from "../hooks/useAuth";
import type { DriveFolderNode, DriveStructureResponse, DiffList } from "../types/drive";

type SelectedFolder = {
  id: string;
  name: string;
};

const DriveExplorerPage = () => {
  const navigate = useNavigate();
  const { user, authenticated, loading: authLoading, refresh } = useAuth();
  const [selectedFolder, setSelectedFolder] = useState<SelectedFolder | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for drive structure from MongoDB
  const [driveStructure, setDriveStructure] = useState<DriveFolderNode | null>(null);
  const [proposedStructure, setProposedStructure] = useState<DriveFolderNode | null>(null);
  const [diffList, setDiffList] = useState<DiffList | null>(null);
  const [structureLoading, setStructureLoading] = useState(false);
  const [structureError, setStructureError] = useState<string | null>(null);

  // State for make change button
  const [makeChangeLoading, setMakeChangeLoading] = useState(false);
  const [makeChangeError, setMakeChangeError] = useState<string | null>(null);

  const diffListRef = useRef<DiffList | null>(null);

  useEffect(() => {
    diffListRef.current = diffList;
  }, [diffList]);

  useEffect(() => {
    if (!authLoading && !authenticated) {
      navigate("/", { replace: true });
    }
  }, [authenticated, authLoading, navigate]);

  // Fetch drive structure from MongoDB on mount
  const fetchDriveStructure = useCallback(async () => {
    setStructureLoading(true);
    setStructureError(null);

    try {
      const data = await apiFetch<DriveStructureResponse>("/api/drive/structure");
      setDriveStructure(data.current_structure);
      setProposedStructure(data.proposed_structure);
      setDiffList(data.diff_list);
    } catch (err) {
      console.error(err);
      const errorMessage = (err as Error).message ?? "Failed to fetch drive structure";
      setStructureError(errorMessage);

      // Handle 401 unauthorized - redirect to login
      if (errorMessage.includes("401") || errorMessage.toLowerCase().includes("unauthorized")) {
        navigate("/", { replace: true });
      }
    } finally {
      setStructureLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    if (authenticated && !authLoading) {
      void fetchDriveStructure();
    }
  }, [authenticated, authLoading, fetchDriveStructure]);

  useEffect(() => {
    if (!selectedFolder) return; 

    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const pollApi = async () => {
      try {
        const data = await apiFetch<DriveStructureResponse>("/api/drive/structure");
        if (isMounted) {
          setDriveStructure(data.current_structure);
          setProposedStructure(data.proposed_structure);
          setDiffList(data.diff_list);
          console.log("Received:", data);
        }
      } catch (err) {
        console.error("Error polling API:", err);
      } finally {
        if (isMounted) {
          timeoutId = setTimeout(pollApi, 10000);
        }
      }
    };

    pollApi(); // start polling

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [selectedFolder]);

  const initializeFolder = useCallback(async (folder: SelectedFolder) => {
    setSelectedFolder(folder);
    setLoading(true);
    setError(null);

    try {
      await apiFetch<DriveFolderNode>(
        `/api/drive/initialize?folderId=${encodeURIComponent(folder.id)}`
      );
      // Refresh the drive structure from database after initialization
      await fetchDriveStructure();
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? "Failed to build folder snapshot");
    } finally {
      setLoading(false);
    }
  }, [fetchDriveStructure]);

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

  const handleMakeChange = useCallback(async () => {
    setMakeChangeLoading(true);
    setMakeChangeError(null);

    try {
      console.log("Making change...")
      console.log(diffListRef.current);
      await apiFetch("/api/drive/make_change", { method: "POST", body: JSON.stringify(diffListRef.current) });
      // Refresh the drive structure after making changes
      await fetchDriveStructure();
    } catch (err) {
      console.error(err);
      setMakeChangeError((err as Error).message ?? "Failed to create folder");
    } finally {
      setMakeChangeLoading(false);
      window.location.reload();
    }
  }, [fetchDriveStructure]);

  const statistics = useMemo(() => {
    if (!driveStructure) {
      return null;
    }
    const childFolders = driveStructure.children_folders.length;
    const rootFiles = driveStructure.files.length;
    const childFiles = driveStructure.children_folders.reduce(
      (count, folder) => count + folder.files.length,
      0
    );
    return { childFolders, rootFiles, childFiles };
  }, [driveStructure]);

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
            {selectedFolder ? (
              <>
                <PickerButton onPicked={handlePicked} buttonText="Change Folder" disabled={loading} />
                {loading ? <span className="muted">Building snapshot...</span> : null}
                {error ? <span className="notice" style={{ fontSize: "0.85rem" }}>{error}</span> : null}
              </>
            ) : null}
            <button type="button" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      {!selectedFolder ? (
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
      ) : null}

      {selectedFolder ? (
        <div className="split-layout">
          <div className="split-pane split-pane-left">
            <AgentChatEmbed />
          </div>
          <div className="split-pane split-pane-right">
            <section className="card stack">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h2>Your Drive Structure</h2>
                <button type="button" onClick={handleMakeChange} disabled={makeChangeLoading}>
                  {makeChangeLoading ? "Making Changes..." : "Make Changes"}
                </button>
              </div>
              {makeChangeError ? <span className="notice">{makeChangeError}</span> : null}
              {structureLoading ? (
                <div className="stack">
                  <span className="muted">Loading your drive structure...</span>
                </div>
              ) : structureError ? (
                <div className="stack">
                  <span className="notice">{structureError}</span>
                  <button type="button" onClick={() => void fetchDriveStructure()}>
                    Retry
                  </button>
                </div>
              ) : !driveStructure ? (
                <div className="stack">
                  <p className="muted">No drive structure found.</p>
                  <p className="muted">
                    Use the folder picker above to scan a folder and save its structure to the database.
                  </p>
                </div>
              ) : (
                <>
                  {statistics ? (
                    <p className="muted">
                      Root contains {statistics.childFolders} subfolders, {statistics.rootFiles} files at the root level, and{" "}
                      {statistics.childFiles} files within those subfolders.
                    </p>
                  ) : null}
                  <DriveList
                    folders={driveStructure.children_folders.map((folder) => ({
                      id: folder.id,
                      name: folder.name,
                    }))}
                    files={driveStructure.files.map((file) => ({
                      id: file.id,
                      name: file.name,
                    }))}
                  />
                </>
              )}
            </section>
          </div>
        </div>
      ) : null}
    </main>
  );
};

export default DriveExplorerPage;
