def test_conversation_list_and_get(client, monkeypatch):
    monkeypatch.setattr("services.conversation_service.list_conversations", lambda: [{"id": "abc", "title": "demo", "updatedAt": "2026-02-14T00:00:00+00:00"}])
    monkeypatch.setattr(
        "services.conversation_service.get_conversation",
        lambda conversation_id: {
            "id": conversation_id,
            "title": "demo",
            "createdAt": "2026-02-14T00:00:00+00:00",
            "updatedAt": "2026-02-14T00:00:00+00:00",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    listed = client.get("/conversations")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == "abc"

    detailed = client.get("/conversations/abc")
    assert detailed.status_code == 200
    assert detailed.json()["id"] == "abc"
