import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AgentSocketEvent, ChatMessage } from "../types/agent";

const WS_PATH = "/api/agent/chat";

export const useAgentChat = (enabled: boolean) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pendingAssistantId = useRef<string | null>(null);

  const createId = useCallback(() => {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
    return Math.random().toString(36).slice(2);
  }, []);

  const backendOrigin = useMemo(() => {
    const origin = import.meta.env.VITE_BACKEND_ORIGIN ?? "http://localhost:8000";
    return origin.replace(/^http/, "ws") + WS_PATH;
  }, []);

  const closeSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  useEffect(() => {
    if (!enabled) {
      closeSocket();
      setConnected(false);
      return () => undefined;
    }

    const socket = new WebSocket(backendOrigin);
    wsRef.current = socket;

    socket.addEventListener("open", () => {
      setConnected(true);
      setError(null);
      console.log("agent-socket-open");
    });

    socket.addEventListener("close", (event) => {
      console.log("agent-socket-close", event.code, event.reason);
      setConnected(false);
      if (event.code === 4401) {
        setError("Session not authenticated. Please sign in again.");
      }
    });

    socket.addEventListener("error", () => {
      setError("Connection error. Please refresh and try again.");
    });

    socket.addEventListener("message", (event) => {
      try {
        const data: AgentSocketEvent = JSON.parse(event.data);
        console.log("agent-event", data);
        if (data.type === "ack") {
          const message: ChatMessage = {
            id: createId(),
            role: "user",
            content: data.message,
          };
          setMessages((prev) => [...prev, message]);
        } else if (data.type === "assistant") {
          if (data.event === "done") {
            pendingAssistantId.current = null;
            console.log("agent-event-done");
            return;
          }
          const delta = data.delta ?? "";
          if (!delta) {
            return;
          }
          console.log("agent-delta", delta);
          if (!pendingAssistantId.current) {
            const id = createId();
            pendingAssistantId.current = id;
            setMessages((prev) => [...prev, { id, role: "assistant", content: delta }]);
          } else {
            const assistantId = pendingAssistantId.current;
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? { ...message, content: (message.content ?? "") + delta }
                  : message
              )
            );
          }
        } else if (data.type === "error") {
          setError(data.message || "Agent error");
        }
      } catch (err) {
        console.error("Failed to parse agent event", err);
      }
    });

    return () => {
      socket.close();
    };
  }, [backendOrigin, enabled, closeSocket]);

  useEffect(() => {
    console.log("agent-messages", messages);
  }, [messages]);

  const sendMessage = useCallback((input: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.log("agent-send skipped", wsRef.current?.readyState);
      setError("Connection not ready. Please wait.");
      return;
    }
    console.log("agent-send", input);
    wsRef.current.send(JSON.stringify({ message: input }));
  }, []);

  return {
    messages,
    connected,
    error,
    sendMessage,
    closeSocket,
  };
};
