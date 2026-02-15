import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChatComposer } from "../chat/ChatComposer";

describe("accessibility", () => {
  it("renders send button with accessible name", () => {
    render(
      <ChatComposer
        value=""
        disabled={false}
        isSending={false}
        onChange={() => undefined}
        onSend={() => undefined}
      />
    );

    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
  });
});
