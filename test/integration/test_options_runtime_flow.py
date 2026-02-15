def test_start_and_stop_service(client, monkeypatch):
    monkeypatch.setattr("services.runtime_service.start", lambda model_alias=None: {"status": "running", "mode": "CPU", "activeModelId": "m1", "message": "ok", "lastUpdatedAt": "2026-02-14T00:00:00+00:00"})
    monkeypatch.setattr("services.runtime_service.stop", lambda: {"status": "stopped", "mode": "unknown", "activeModelId": None, "message": "stopped", "lastUpdatedAt": "2026-02-14T00:00:00+00:00"})

    start = client.post("/service/start")
    stop = client.post("/service/stop")

    assert start.status_code == 200
    assert stop.status_code == 200
