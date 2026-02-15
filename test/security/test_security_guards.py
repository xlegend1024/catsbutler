def test_csp_header_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "content-security-policy" in response.headers


def test_validation_guard_returns_422(client):
    response = client.post("/chat", json={"messages": [{"role": "user", "content": ""}]})
    assert response.status_code in (400, 422)
