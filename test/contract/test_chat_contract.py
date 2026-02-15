def test_chat_requires_messages(client):
    response = client.post("/chat", json={"messages": []})
    assert response.status_code in (400, 422)


def test_chat_success(client, monkeypatch):
    def fake_reply(messages, conversation_id=None):
        return {"reply": "ok", "chart": None, "conversationId": "demo"}

    monkeypatch.setattr("services.chat_service.create_reply", fake_reply)
    response = client.post("/chat", json={"messages": [{"role": "user", "content": "hello"}]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"] == "ok"
    assert payload["conversationId"] == "demo"
