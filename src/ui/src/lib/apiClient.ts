const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }

  return (await response.json()) as T;
}

export type ServiceState = {
  status: "stopped" | "starting" | "running" | "stopping" | "error";
  mode: "NPU" | "GPU" | "CPU" | "unknown";
  activeModelId?: string | null;
  message?: string | null;
  lastUpdatedAt: string;
};

export type ModelProfile = {
  id: string;
  displayName: string;
  availability: "available" | "downloading" | "unavailable";
  recommendedMode: "NPU" | "GPU" | "CPU" | "unknown";
};

export type ChatMessage = { role: "user" | "assistant" | "system" | "tool"; content: string };

export type ChartPayload = {
  type: "line";
  points: Array<{ timestamp: string; price: number }>;
};

export type ChatResponse = {
  reply: string;
  chart?: ChartPayload | null;
  conversationId?: string | null;
};

export type AppConfig = {
  selectedModelId: string;
  autoStartService: boolean;
  maxTokens?: number;
  updatedAt: string;
};

export type McpServerConfig = {
  type: string;
  command: string;
  args: string[];
  env: Record<string, string>;
};

export type McpConfig = {
  mcp: {
    servers: Record<string, McpServerConfig>;
  };
};

export type McpTool = {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  serverName: string;
};

export type ConversationSummary = { id: string; title: string; updatedAt: string };
export type ConversationRecord = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
};

export const apiClient = {
  health: () => request<{ status: string }>("/health"),
  getServiceStatus: () => request<ServiceState>("/service/status"),
  startService: () => request<ServiceState>("/service/start", { method: "POST" }),
  stopService: () => request<ServiceState>("/service/stop", { method: "POST" }),
  listModels: () => request<{ items: ModelProfile[] }>("/models"),
  getConfig: () => request<AppConfig>("/config"),
  putConfig: (payload: Partial<AppConfig>) => request<AppConfig>("/config", { method: "PUT", body: JSON.stringify(payload) }),
  chat: (messages: ChatMessage[], conversationId?: string | null) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ messages, conversationId: conversationId || undefined }),
    }),
  getStockQuote: (symbol: string) => request(`/stocks/quote?symbol=${encodeURIComponent(symbol)}`),
  listConversations: () => request<{ items: ConversationSummary[] }>("/conversations"),
  getConversation: (id: string) => request<ConversationRecord>(`/conversations/${encodeURIComponent(id)}`),
  getMcpConfig: () => request<McpConfig>("/mcp/config"),
  putMcpConfig: (payload: McpConfig) => request<McpConfig>("/mcp/config", { method: "PUT", body: JSON.stringify(payload) }),
  listMcpTools: () => request<{ items: McpTool[] }>("/mcp/tools"),
  reloadMcpServers: () => request<{ items: McpTool[] }>("/mcp/reload", { method: "POST" }),
};
