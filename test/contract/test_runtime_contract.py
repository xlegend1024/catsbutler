def test_service_status_contract(client):
    response = client.get("/service/status")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "mode" in payload


def test_models_contract(client):
    response = client.get("/models")
    assert response.status_code == 200
    assert "items" in response.json()
