import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Divider,
  FluentProvider,
  Subtitle2,
  Text,
  Title1,
  webLightTheme,
  tokens,
} from "@fluentui/react-components";
import {
  ChatRegular,
  NavigationRegular,
  SettingsRegular,
} from "@fluentui/react-icons";
import "./App.css";
import { apiClient, type ConversationSummary, type McpTool, type ModelProfile, type ServiceState } from "./lib/apiClient";
import { ChatComposer } from "./components/chat/ChatComposer";
import { ChatTimeline } from "./components/chat/ChatTimeline";
import { useChatController } from "./components/chat/useChatController";
import { HistoryMenu } from "./components/history/HistoryMenu";
import { OptionsPanel } from "./components/options/OptionsPanel";

type ConfigState = {
  maxTokens: number;
};

export default function App() {
  const [serviceState, setServiceState] = useState<ServiceState | null>(null);
  const [models, setModels] = useState<ModelProfile[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [history, setHistory] = useState<ConversationSummary[]>([]);
  const [showOptions, setShowOptions] = useState(true);
  const [mcpConfigJson, setMcpConfigJson] = useState("{}");
  const [mcpTools, setMcpTools] = useState<McpTool[]>([]);
  const [isReloadingMcp, setIsReloadingMcp] = useState(false);

  const [config, setConfig] = useState<ConfigState>({
    maxTokens: 2048,
  });

  const refreshHistory = async () => {
    const conversations = await apiClient.listConversations();
    setHistory(conversations.items);
  };

  const chat = useChatController(selectedModelId, refreshHistory);

  async function refreshAll() {
    const results = await Promise.allSettled([
      apiClient.getServiceStatus(),
      apiClient.listModels(),
      apiClient.getConfig(),
      apiClient.listConversations(),
      apiClient.getMcpConfig(),
      apiClient.listMcpTools(),
    ]);

    const [state, modelList, appConfig, conversations, mcpConfig, mcpToolsList] = results;

    if (state.status === "fulfilled") setServiceState(state.value);
    if (modelList.status === "fulfilled") setModels(modelList.value.items);
    if (appConfig.status === "fulfilled") {
      setSelectedModelId(appConfig.value.selectedModelId);
      setConfig({ maxTokens: appConfig.value.maxTokens ?? 2048 });
    }
    if (conversations.status === "fulfilled") setHistory(conversations.value.items);
    if (mcpConfig.status === "fulfilled") setMcpConfigJson(JSON.stringify(mcpConfig.value, null, 2));
    if (mcpToolsList.status === "fulfilled") setMcpTools(mcpToolsList.value.items);

    // Log any failures for debugging
    results.forEach((r, i) => {
      if (r.status === "rejected") {
        const names = ["serviceStatus", "models", "config", "conversations", "mcpConfig", "mcpTools"];
        console.warn(`refreshAll: ${names[i]} failed:`, r.reason);
      }
    });
  }

  useEffect(() => {
    refreshAll().catch(() => {
      // best effort load
    });
  }, []);

  async function onStartService() {
    const state = await apiClient.startService();
    setServiceState(state);
  }

  async function onStopService() {
    const state = await apiClient.stopService();
    setServiceState(state);
  }

  async function onSelectModel(modelId: string) {
    setSelectedModelId(modelId);
    await apiClient.putConfig({ selectedModelId: modelId });
    await refreshAll();
  }

  function onMaxTokensChange(value: number) {
    setConfig((current) => ({ ...current, maxTokens: value }));
    // Auto-save maxTokens change
    apiClient.putConfig({
      selectedModelId: selectedModelId || models[0]?.id || "",
      maxTokens: value,
    }).catch(() => {});
  }

  async function onSaveMcpConfig() {
    try {
      const parsed = JSON.parse(mcpConfigJson);
      await apiClient.putMcpConfig(parsed);
      // Backend auto-discovers tools after saving; refresh the tool list
      const result = await apiClient.listMcpTools();
      setMcpTools(result.items);
    } catch {
      // JSON parse error handled by ConfigPanel validation
    }
  }

  async function onReloadMcpServers() {
    setIsReloadingMcp(true);
    try {
      const result = await apiClient.reloadMcpServers();
      setMcpTools(result.items);
    } catch {
      // reload failed
    } finally {
      setIsReloadingMcp(false);
    }
  }

  async function onLoadConversation(id: string) {
    const payload = await apiClient.getConversation(id);
    chat.loadConversation({ id: payload.id, messages: payload.messages });
  }

  const chatDisabled = !selectedModelId || serviceState?.status !== "running";

  const statusColor = serviceState?.status === "running" ? "success" : serviceState?.status === "error" ? "danger" : "informative";

  return (
    <FluentProvider
      theme={{
        ...webLightTheme,
        fontFamilyBase: '"Segoe UI", sans-serif',
      }}
    >
      <div className="page">
        <Card className="hero-card" size="large">
          <div className="hero-row">
            <div className="hero-title">
              <span className="hero-icon">🐱</span>
              <div>
                <Title1>CatsButler</Title1>
                <Text className="hero-sub">Local AI Chat · Stock Insights</Text>
              </div>
            </div>
            <div className="hero-actions">
              <Badge
                appearance="filled"
                color={statusColor}
                size="medium"
              >
                {serviceState?.status ?? "offline"}
              </Badge>
              <Button
                appearance="subtle"
                icon={showOptions ? <ChatRegular /> : <SettingsRegular />}
                onClick={() => setShowOptions((prev) => !prev)}
              >
                {showOptions ? "Chat focus" : "Options"}
              </Button>
            </div>
          </div>
        </Card>

        <div className={`layout ${showOptions ? "panel-open" : ""}`}>
          {showOptions ? (
            <div className="panel-column">
              <OptionsPanel
                serviceState={serviceState}
                models={models}
                selectedModelId={selectedModelId}
                maxTokens={config.maxTokens}
                mcpConfigJson={mcpConfigJson}
                mcpTools={mcpTools}
                isReloadingMcp={isReloadingMcp}
                onStartService={onStartService}
                onStopService={onStopService}
                onSelectModel={onSelectModel}
                onMaxTokensChange={onMaxTokensChange}
                onMcpConfigChange={setMcpConfigJson}
                onSaveMcpConfig={onSaveMcpConfig}
                onReloadMcpServers={onReloadMcpServers}
              />
              <HistoryMenu items={history} onLoad={onLoadConversation} />
            </div>
          ) : null}

          <Card className="chat-card" size="large">
            <CardHeader
              image={<ChatRegular className="section-icon" />}
              header={<Subtitle2>Chat</Subtitle2>}
              description={
                <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                  {selectedModelId ? `Model: ${selectedModelId}` : "No model selected"}
                </Text>
              }
            />
            <Divider />
            <ChatTimeline messages={chat.messages} />
            <Divider />
            <ChatComposer
              value={chat.input}
              disabled={chatDisabled || !chat.canSend}
              isSending={chat.isSending}
              onChange={chat.setInput}
              onSend={chat.sendMessage}
            />
            {chatDisabled ? (
              <div className="warn-banner">
                <NavigationRegular />
                <Text size={200}>Start service and select a model to begin chatting.</Text>
              </div>
            ) : null}
          </Card>
        </div>
      </div>
    </FluentProvider>
  );
}
