export type ChatRole = "user" | "assistant" | "system" | "event" | "error";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

export type ChatDeltaEvent = {
  type: "assistant";
  delta?: string;
  event?: "done";
};

export type ChatAckEvent = {
  type: "ack";
  message: string;
};

export type ChatErrorEvent = {
  type: "error";
  message: string;
};

export type AgentSocketEvent = ChatDeltaEvent | ChatAckEvent | ChatErrorEvent;
