import { Badge, Button, Text, tokens } from "@fluentui/react-components";
import {
  PlayRegular,
  StopRegular,
  TopSpeedRegular,
} from "@fluentui/react-icons";
import type { ServiceState } from "../../lib/apiClient";

type Props = {
  state: ServiceState | null;
  onStart: () => void;
  onStop: () => void;
};

export function ServiceControls({ state, onStart, onStop }: Props) {
  const running = state?.status === "running";
  const statusColor = running ? "success" : state?.status === "error" ? "danger" : "informative";
  return (
    <div className="options-block">
      <div className="status-row">
        <Badge appearance="tint" color={statusColor} size="small">
          {state?.status ?? "unknown"}
        </Badge>
        <span className="status-detail">
          <TopSpeedRegular style={{ fontSize: 14, color: tokens.colorNeutralForeground3 }} />
          <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>{state?.mode ?? "unknown"}</Text>
        </span>
      </div>
      <div className="button-row">
        <Button appearance="primary" icon={<PlayRegular />} onClick={onStart} disabled={running} size="small">
          Start
        </Button>
        <Button appearance="outline" icon={<StopRegular />} onClick={onStop} disabled={!running} size="small">
          Stop
        </Button>
      </div>
    </div>
  );
}
