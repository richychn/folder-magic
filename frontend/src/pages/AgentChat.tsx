import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import ChatComposer from "../components/ChatComposer";
import ChatTranscript from "../components/ChatTranscript";
import { useAgentChat } from "../hooks/useAgentChat";
import { useAuth } from "../hooks/useAuth";

const AgentChatPage = () => {
  const navigate = useNavigate();
  const { authenticated, loading, user } = useAuth();
  const { messages, connected, error, sendMessage } = useAgentChat(authenticated && !loading);

  useEffect(() => {
    if (!loading && !authenticated) {
      navigate("/", { replace: true });
    }
  }, [authenticated, loading, navigate]);

  return (
    <main className="stack">
      <header>
        <div className="stack">
          <h1>Drive Assistant</h1>
          <span className="muted">
            Chat with an agent about your Drive folder snapshots. Future versions will let it read data and call
            tools.
          </span>
        </div>
        <span className={`chat-status ${connected ? "" : error ? "error" : "disconnected"}`}>
          <span className="indicator" />
          {error ? error : connected ? "Connected" : "Connecting..."}
        </span>
      </header>

      <section className="card chat-panel">
        <ChatTranscript messages={messages} />
        <ChatComposer onSend={sendMessage} disabled={!connected} />
      </section>

      {user?.email ? <span className="muted">Signed in as {user.email}</span> : null}
    </main>
  );
};

export default AgentChatPage;
