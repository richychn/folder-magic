import { FormEvent, useState } from "react";

type ChatComposerProps = {
  onSend: (message: string) => void;
  disabled?: boolean;
};

const ChatComposer = ({ onSend, disabled }: ChatComposerProps) => {
  const [value, setValue] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) {
      return;
    }
    onSend(trimmed);
    setValue("");
  };

  return (
    <form className="chat-composer" onSubmit={handleSubmit}>
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Ask the agent a question..."
        rows={3}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || value.trim().length === 0}>
        Send
      </button>
    </form>
  );
};

export default ChatComposer;
