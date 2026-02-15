import { Button, Input, Spinner } from "@fluentui/react-components";
import { SendRegular } from "@fluentui/react-icons";

type Props = {
  value: string;
  disabled: boolean;
  isSending: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
};

export function ChatComposer({ value, disabled, isSending, onChange, onSend }: Props) {
  return (
    <div className="chat-input">
      <Input
        value={value}
        onChange={(_, data) => onChange(data.value)}
        placeholder="Ask me anything…"
        appearance="filled-lighter"
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            if (!disabled) {
              onSend();
            }
          }
        }}
      />
      <Button
        appearance="primary"
        disabled={disabled}
        onClick={onSend}
        icon={isSending ? <Spinner size="tiny" /> : <SendRegular />}
        shape="circular"
        size="medium"
      />
    </div>
  );
}
