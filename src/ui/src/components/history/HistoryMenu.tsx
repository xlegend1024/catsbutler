import { Button, Card, CardHeader, Divider, Subtitle2, Text, tokens } from "@fluentui/react-components";
import { HistoryRegular, ChatBubblesQuestionRegular } from "@fluentui/react-icons";
import type { ConversationSummary } from "../../lib/apiClient";

type Props = {
  items: ConversationSummary[];
  onLoad: (id: string) => void;
};

export function HistoryMenu({ items, onLoad }: Props) {
  return (
    <Card className="history-menu" size="small" aria-label="Conversation history">
      <CardHeader
        image={<HistoryRegular className="section-icon" />}
        header={<Subtitle2>History</Subtitle2>}
      />
      <Divider />
      <div className="history-items">
        {items.length === 0 ? (
          <Text size={200} style={{ color: tokens.colorNeutralForeground3, padding: "8px 4px" }}>
            No conversations yet.
          </Text>
        ) : (
          items.slice(0, 5).map((item) => {
            const dateStr = item.updatedAt
              ? new Date(item.updatedAt).toISOString().slice(0, 10)
              : "";
            return (
              <Button
                key={item.id}
                appearance="subtle"
                icon={<ChatBubblesQuestionRegular />}
                onClick={() => onLoad(item.id)}
                className="history-item"
                size="small"
              >
                <span className="history-item-content">
                  <span className="history-item-text">{item.title}</span>
                  {dateStr && <span className="history-item-date">{dateStr}</span>}
                </span>
              </Button>
            );
          })
        )}
      </div>
    </Card>
  );
}
