def test_history_restore_flow(client, monkeypatch):
    monkeypatch.setattr(
        "services.conversation_service.get_conversation",
        lambda conversation_id: {
            "id": conversation_id,
            "title": "history",
            "createdAt": "2026-02-14T00:00:00+00:00",
            "updatedAt": "2026-02-14T00:00:00+00:00",
            "messages": [{"role": "assistant", "content": "hi"}],
        },
    )

    response = client.get("/conversations/history-1")
    assert response.status_code == 200
    assert response.json()["messages"][0]["content"] == "hi"
