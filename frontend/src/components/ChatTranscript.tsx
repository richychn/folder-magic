import type { ChatMessage } from "../hooks/useAgentChat";

type ChatTranscriptProps = {
  messages: ChatMessage[];
};

const roleLabel: Record<ChatMessage["role"], string> = {
  user: "You",
  assistant: "Agent",
  system: "System",
  event: "Event",
  error: "Error",
};

const ChatTranscript = ({ messages }: ChatTranscriptProps) => {
  console.log("render-transcript", messages);
  return (
    <div className="chat-transcript">
      {messages.length === 0 ? (
        <p className="muted">Start the conversation by asking the agent anything about your Drive snapshot.</p>
      ) : null}
      <ul className="chat-list">
        {messages.map((message) => (
          <li key={message.id} className={`chat-entry chat-${message.role}`}>
            <strong>{roleLabel[message.role]}:</strong> {message.content}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ChatTranscript;
