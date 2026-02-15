import {
  Accordion,
  AccordionHeader,
  AccordionItem,
  AccordionPanel,
  Card,
  CardHeader,
  Field,
  SpinButton,
  Subtitle2,
  Text,
  tokens,
} from "@fluentui/react-components";
import {
  BrainCircuitRegular,
  PlugConnectedRegular,
  SettingsRegular,
  WrenchRegular,
} from "@fluentui/react-icons";
import type { McpTool, ModelProfile, ServiceState } from "../../lib/apiClient";
import { ConfigPanel } from "./ConfigPanel";
import { ModelSelector } from "./ModelSelector";
import { ServiceControls } from "./ServiceControls";

type Props = {
  serviceState: ServiceState | null;
  models: ModelProfile[];
  selectedModelId: string | null;
  maxTokens: number;
  mcpConfigJson: string;
  mcpTools: McpTool[];
  isReloadingMcp: boolean;
  onStartService: () => void;
  onStopService: () => void;
  onSelectModel: (modelId: string) => void;
  onMaxTokensChange: (value: number) => void;
  onMcpConfigChange: (json: string) => void;
  onSaveMcpConfig: () => void;
  onReloadMcpServers: () => void;
};

export function OptionsPanel(props: Props) {
  return (
    <Card className="side-panel" size="small" aria-label="Options panel">
      <CardHeader
        image={<SettingsRegular className="section-icon" />}
        header={<Subtitle2>Options</Subtitle2>}
      />

      <Field label="Max Tokens" size="small" style={{ padding: "8px 6px 0" }}>
        <SpinButton
          size="small"
          value={props.maxTokens}
          min={64}
          max={8192}
          step={64}
          onChange={(_e, data) => {
            if (data.value !== undefined && data.value !== null) {
              props.onMaxTokensChange(data.value);
            }
          }}
        />
        <Text size={100} style={{ color: tokens.colorNeutralForeground3 }}>
          Limits model response length (64–8192)
        </Text>
      </Field>

      <Accordion multiple defaultOpenItems={["service", "model"]} collapsible>
        <AccordionItem value="service">
          <AccordionHeader icon={<PlugConnectedRegular className="block-icon" />}>
            Service
          </AccordionHeader>
          <AccordionPanel>
            <ServiceControls state={props.serviceState} onStart={props.onStartService} onStop={props.onStopService} />
          </AccordionPanel>
        </AccordionItem>

        <AccordionItem value="model">
          <AccordionHeader icon={<BrainCircuitRegular className="block-icon" />}>
            Model
          </AccordionHeader>
          <AccordionPanel>
            <ModelSelector models={props.models} selectedModelId={props.selectedModelId} onSelect={props.onSelectModel} />
          </AccordionPanel>
        </AccordionItem>

        <AccordionItem value="mcp">
          <AccordionHeader icon={<WrenchRegular className="block-icon" />}>
            MCP Servers
          </AccordionHeader>
          <AccordionPanel>
            <ConfigPanel
              mcpConfigJson={props.mcpConfigJson}
              mcpTools={props.mcpTools}
              onChange={props.onMcpConfigChange}
              onSave={props.onSaveMcpConfig}
              onReload={props.onReloadMcpServers}
              isReloading={props.isReloadingMcp}
            />
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </Card>
  );
}
