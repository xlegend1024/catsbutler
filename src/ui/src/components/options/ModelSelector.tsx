import { Badge, Dropdown, Option, Text } from "@fluentui/react-components";
import type { ModelProfile } from "../../lib/apiClient";

type Props = {
  models: ModelProfile[];
  selectedModelId: string | null;
  onSelect: (modelId: string) => void;
};

function modeColor(mode: string): "informative" | "success" | "warning" {
  if (mode.includes("NPU") || mode.includes("npu") || mode.includes("qnn")) return "success";
  if (mode.includes("GPU") || mode.includes("gpu")) return "informative";
  return "warning";
}

export function ModelSelector({ models, selectedModelId, onSelect }: Props) {
  return (
    <div className="options-block">
      <Dropdown
        value={selectedModelId ?? ""}
        selectedOptions={selectedModelId ? [selectedModelId] : []}
        onOptionSelect={(_, data) => {
          if (data.optionValue) {
            onSelect(data.optionValue);
          }
        }}
        placeholder="Select a local model"
        size="small"
      >
        {models.map((model) => (
          <Option key={model.id} value={model.id} text={model.displayName}>
            <div className="model-option">
              <Text size={200}>{model.displayName}</Text>
              <Badge appearance="tint" color={modeColor(model.recommendedMode)} size="extra-small">
                {model.recommendedMode}
              </Badge>
            </div>
          </Option>
        ))}
      </Dropdown>
    </div>
  );
}
