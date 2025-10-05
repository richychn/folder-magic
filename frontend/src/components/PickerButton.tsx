import { useState } from "react";

import { apiFetch } from "../api/client";

type PickerButtonProps = {
  onPicked: (folder: { id: string; name: string }) => void;
  disabled?: boolean;
};

type PickerTokenResponse = {
  access_token: string;
};

let pickerLoader: Promise<void> | null = null;

async function loadPickerApi(): Promise<void> {
  if (pickerLoader) {
    return pickerLoader;
  }

  pickerLoader = new Promise<void>((resolve, reject) => {
    const scriptId = "google-api-script";
    const existing = document.getElementById(scriptId);

    const handleReady = () => {
      if (!window.gapi) {
        reject(new Error("Google API not available on window"));
        return;
      }
      window.gapi.load("picker", {
        callback: () => resolve(),
        onerror: () => reject(new Error("Failed to load Google Picker")),
        timeout: 10000,
        ontimeout: () => reject(new Error("Timed out loading Google Picker")),
      });
    };

    if (existing) {
      if (window.gapi) {
        handleReady();
      } else {
        existing.addEventListener("load", handleReady, { once: true });
      }
      return;
    }

    const script = document.createElement("script");
    script.id = scriptId;
    script.src = "https://apis.google.com/js/api.js";
    script.async = true;
    script.defer = true;
    script.onload = handleReady;
    script.onerror = () => reject(new Error("Failed to load Google API"));
    document.body.appendChild(script);
  });

  try {
    await pickerLoader;
  } catch (err) {
    pickerLoader = null;
    throw err;
  }
}

const PickerButton = ({ onPicked, disabled }: PickerButtonProps) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const developerKey = import.meta.env.VITE_GOOGLE_API_KEY as string | undefined;

  const openPicker = async () => {
    if (!developerKey) {
      setError("Google API key is missing. Set VITE_GOOGLE_API_KEY in the frontend environment.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await loadPickerApi();

      const { access_token } = await apiFetch<PickerTokenResponse>("/api/auth/picker-token");
      const googlePicker = window.google.picker;

      const view = new googlePicker.DocsView(googlePicker.ViewId.FOLDERS)
        .setIncludeFolders(true)
        .setSelectFolderEnabled(true);

      const picker = new googlePicker.PickerBuilder()
        .addView(view)
        .enableFeature(googlePicker.Feature.SUPPORT_TEAM_DRIVES)
        .setOAuthToken(access_token)
        .setDeveloperKey(developerKey)
        .setOrigin(window.location.protocol + "//" + window.location.host)
        .setCallback((data: any) => {
          if (data.action === googlePicker.Action.PICKED && data.docs?.length) {
            const doc = data.docs[0];
            onPicked({ id: doc.id, name: doc.name });
          }
        })
        .build();

      picker.setVisible(true);
    } catch (err) {
      console.error(err);
      pickerLoader = null;
      setError((err as Error).message ?? "Failed to open Google Picker");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="stack">
      <button onClick={openPicker} disabled={loading || disabled}>
        {loading ? "Opening Picker..." : "Choose Google Drive Folder"}
      </button>
      {error ? <span className="notice">{error}</span> : null}
    </div>
  );
};

export default PickerButton;
