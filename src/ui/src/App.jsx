import { useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Input,
  Text,
  Title1,
  Subtitle1,
} from "@fluentui/react-components";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! Ask me anything." },
  ]);
  const [agentName, setAgentName] = useState("agent");
  const [systemPrompt, setSystemPrompt] = useState("Loading system prompt...");
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const listRef = useRef(null);

  const canSend = useMemo(() => input.trim().length > 0 && !isSending, [input, isSending]);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    const loadAgent = async () => {
      try {
        const response = await fetch(`${API_URL}/agent`);
        if (!response.ok) {
          throw new Error(`Failed to load agent: ${response.status}`);
        }
        const data = await response.json();
        setAgentName(data.name || "agent");
        setSystemPrompt(data.system_prompt || "");
      } catch (error) {
        setSystemPrompt(`Error: ${error.message}`);
      }
    };

    loadAgent();
  }, []);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text) {
      return;
    }

    const nextMessages = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setIsSending(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages }),
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(`${response.status} ${response.statusText}: ${body}`);
      }

      const data = await response.json();
      setMessages([...nextMessages, { role: "assistant", content: data.reply }]);
    } catch (error) {
      setMessages([
        ...nextMessages,
        { role: "assistant", content: `Error: ${error.message}` },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const onKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) {
        sendMessage();
      }
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <div>
          <Title1>Foundry Local Chat</Title1>
          {/* <Subtitle1>Fluent UI React + NPU model</Subtitle1> */}
        </div>
      </header>

      <div className={`layout ${isPanelOpen ? "panel-open" : ""}`}>
        <div className="panel-column">
          <Button
            className="panel-toggle"
            appearance="secondary"
            onClick={() => setIsPanelOpen((prev) => !prev)}
            aria-expanded={isPanelOpen}
            aria-controls="agent-panel"
          >
            {isPanelOpen ? "Hide" : "Show"} agent panel
          </Button>
          {isPanelOpen && (
            <aside className="side-panel" id="agent-panel">
              <div className="panel-header">
                <Text weight="semibold">Agent</Text>
                <Text size={200}>{agentName}</Text>
              </div>
              <div className="panel-body">
                <Text className="prompt-text">{systemPrompt}</Text>
              </div>
            </aside>
          )}
        </div>

        <section className="chat-card">
          <div className="chat-header">
            <Text weight="semibold">Chat</Text>
            <Text size={200}>Model: local Foundry</Text>
          </div>

          <div className="chat-list" ref={listRef}>
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`bubble ${message.role}`}
              >
                <Text>{message.content}</Text>
              </div>
            ))}
          </div>

          <div className="chat-input">
            <Input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Type a message..."
              className="input"
            />
            <Button appearance="primary" onClick={sendMessage} disabled={!canSend}>
              {isSending ? "Sending..." : "Send"}
            </Button>
          </div>
        </section>
      </div>
    </div>
  );
}
