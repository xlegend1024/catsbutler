def test_health_and_chat_flow(client, monkeypatch):
    health = client.get("/health")
    assert health.status_code == 200

    monkeypatch.setattr("services.chat_service.create_reply", lambda messages, conversation_id=None: {"reply": "hello back", "chart": None, "conversationId": "c1"})
    response = client.post("/chat", json={"messages": [{"role": "user", "content": "hello"}]})
    assert response.status_code == 200
    assert response.json()["reply"] == "hello back"
