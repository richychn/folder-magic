import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { BACKEND_ORIGIN } from "../api/client";
import { useAuth } from "../hooks/useAuth";

const HomePage = () => {
  const { authenticated, user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && authenticated) {
      navigate("/drive", { replace: true });
    }
  }, [authenticated, loading, navigate]);

  const handleLogin = () => {
    window.location.href = `${BACKEND_ORIGIN}/api/auth/login`;
  };

  return (
    <main>
      <div className="card stack">
        <h1>Drive Explorer</h1>
        <p className="muted">
          Authenticate with Google to browse folder contents inside Drive. OAuth tokens stay on the server—only a
          secure session cookie reaches the browser.
        </p>
        <div className="actions">
          <button type="button" onClick={handleLogin} disabled={loading}>
            {loading ? "Checking session..." : "Sign in with Google"}
          </button>
          {user?.email ? <span className="tag">Signed in as {user.email}</span> : null}
        </div>
      </div>
    </main>
  );
};

export default HomePage;
