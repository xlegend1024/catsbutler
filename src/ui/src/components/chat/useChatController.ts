import { useMemo, useState } from "react";
import { apiClient, type ChatMessage, type ChartPayload } from "../../lib/apiClient";

type TimelineEntry = ChatMessage & { chart?: ChartPayload | null };

export function useChatController(selectedModelId: string | null, onAfterReply?: () => void) {
  const [messages, setMessages] = useState<TimelineEntry[]>([
    { role: "assistant", content: "Ready when you are." },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const canSend = useMemo(
    () => Boolean(selectedModelId) && !isSending && input.trim().length > 0,
    [selectedModelId, isSending, input]
  );

  async function sendMessage() {
    if (!canSend) {
      return;
    }

    const userMessage: TimelineEntry = { role: "user", content: input.trim() };
    const next = [...messages, userMessage];
    setMessages(next);
    setInput("");
    setIsSending(true);

    try {
      const payload = await apiClient.chat(
        next.map((item) => ({ role: item.role, content: item.content })),
        conversationId
      );
      setMessages([...next, { role: "assistant", content: payload.reply, chart: payload.chart }]);
      if (payload.conversationId) {
        setConversationId(payload.conversationId);
      }
      onAfterReply?.();
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Unknown error";
      setMessages([...next, { role: "assistant", content: `Error: ${detail}` }]);
    } finally {
      setIsSending(false);
    }
  }

  function loadConversation(conversation: { id: string; messages: ChatMessage[] }) {
    setConversationId(conversation.id);
    setMessages(
      conversation.messages.map((item) => ({
        role: item.role,
        content: item.content,
      }))
    );
  }

  return {
    messages,
    input,
    setInput,
    isSending,
    canSend,
    sendMessage,
    loadConversation,
  };
}
