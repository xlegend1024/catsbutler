import { Text, tokens } from "@fluentui/react-components";
import { BotRegular, PersonRegular } from "@fluentui/react-icons";
import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChartPayload, ChatMessage } from "../../lib/apiClient";
import { StockChart } from "./StockChart";

type Entry = ChatMessage & { chart?: ChartPayload | null };

type Props = {
  messages: Entry[];
};

export function ChatTimeline({ messages }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-list" role="log" aria-live="polite">
      {messages.map((message, index) => (
        <div key={`${message.role}-${index}`} className={`bubble ${message.role}`}>
          <div className="bubble-avatar">
            {message.role === "user" ? (
              <PersonRegular style={{ color: tokens.colorNeutralForegroundOnBrand }} />
            ) : (
              <BotRegular style={{ color: tokens.colorBrandForeground1 }} />
            )}
          </div>
          <div className="bubble-body">
            {message.role === "assistant" ? (
              <div className="markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              </div>
            ) : (
              <Text>{message.content}</Text>
            )}
            {message.chart?.points ? <StockChart points={message.chart.points} /> : null}
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
