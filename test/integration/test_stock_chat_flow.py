def test_stock_prompt_returns_chart(client, monkeypatch):
    monkeypatch.setattr(
        "services.chat_service.create_reply",
        lambda messages, conversation_id=None: {
            "reply": "stock ready",
            "chart": {"type": "line", "points": [{"timestamp": "2026-02-14T00:00:00+00:00", "price": 1.0}]},
            "conversationId": "c-stock",
        },
    )

    response = client.post("/chat", json={"messages": [{"role": "user", "content": "show AAPL stock chart"}]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["chart"]["type"] == "line"
