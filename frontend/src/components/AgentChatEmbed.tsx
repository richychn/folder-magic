import ChatComposer from "./ChatComposer";
import ChatTranscript from "./ChatTranscript";
import { useAgentChat } from "../hooks/useAgentChat";
import { useAuth } from "../hooks/useAuth";

type AgentChatEmbedProps = {
  className?: string;
  style?: React.CSSProperties;
};

const AgentChatEmbed = ({ className, style }: AgentChatEmbedProps) => {
  const { authenticated, loading } = useAuth();
  const { messages, connected, error, sendMessage } = useAgentChat(authenticated && !loading);

  return (
    <div className={`card chat-panel ${className ?? ""}`} style={style}>
      <div className="stack" style={{ marginBottom: "0.5rem" }}>
        <h2>Drive Assistant</h2>
        <span className={`chat-status ${connected ? "" : error ? "error" : "disconnected"}`}>
          <span className="indicator" />
          {error ? error : connected ? "Connected" : "Connecting..."}
        </span>
      </div>
      <ChatTranscript messages={messages} />
      <ChatComposer onSend={sendMessage} disabled={!connected} />
    </div>
  );
};

export default AgentChatEmbed;
