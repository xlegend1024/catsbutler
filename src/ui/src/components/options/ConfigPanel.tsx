import { useState } from "react";
import {
  Badge,
  Button,
  Field,
  Text,
  Textarea,
  tokens,
} from "@fluentui/react-components";
import {
  ArrowSyncRegular,
  SaveRegular,
} from "@fluentui/react-icons";
import type { McpTool } from "../../lib/apiClient";

type Props = {
  mcpConfigJson: string;
  mcpTools: McpTool[];
  onChange: (json: string) => void;
  onSave: () => void;
  onReload: () => void;
  isReloading?: boolean;
};

export function ConfigPanel({
  mcpConfigJson,
  mcpTools,
  onChange,
  onSave,
  onReload,
  isReloading,
}: Props) {
  const [jsonError, setJsonError] = useState<string | null>(null);

  function handleChange(value: string) {
    onChange(value);
    try {
      JSON.parse(value);
      setJsonError(null);
    } catch {
      setJsonError("Invalid JSON");
    }
  }

  return (
    <div className="options-block">
      <Field
        label="MCP Server Configuration (mcp.json)"
        size="small"
        validationState={jsonError ? "error" : "success"}
        validationMessage={jsonError}
      >
        <Textarea
          size="small"
          value={mcpConfigJson}
          onChange={(_, data) => handleChange(data.value)}
          rows={10}
          style={{ fontFamily: "'Cascadia Code', 'Consolas', monospace", fontSize: "12px" }}
          resize="vertical"
        />
      </Field>

      <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
        <Button appearance="primary" icon={<SaveRegular />} onClick={onSave} size="small" disabled={!!jsonError}>
          Save
        </Button>
        <Button
          appearance="secondary"
          icon={<ArrowSyncRegular />}
          onClick={onReload}
          size="small"
          disabled={isReloading}
        >
          {isReloading ? "Reloading..." : "Reload Tools"}
        </Button>
      </div>

      {mcpTools.length > 0 && (
        <div style={{ marginTop: "12px" }}>
          <Text size={200} weight="semibold" style={{ color: tokens.colorNeutralForeground2 }}>
            Discovered Tools ({mcpTools.length})
          </Text>
          <div style={{ marginTop: "4px", display: "flex", flexWrap: "wrap", gap: "4px" }}>
            {mcpTools.map((tool) => (
              <Badge key={tool.name} appearance="outline" size="small" title={tool.description}>
                {tool.name}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
