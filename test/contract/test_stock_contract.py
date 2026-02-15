def test_config_get_and_put(client):
    put = client.put(
        "/config",
        json={
            "selectedModelId": "qwen2.5-7b-instruct-qnn-npu:2",
            "autoStartService": False,
            "alpacaApiKey": "k",
            "alpacaApiSecret": "s",
            "alpacaBaseUrl": "https://data.alpaca.markets",
        },
    )
    assert put.status_code == 200

    get = client.get("/config")
    assert get.status_code == 200
    payload = get.json()
    assert payload["selectedModelId"]


def test_stock_quote_contract(client, monkeypatch):
    monkeypatch.setattr("services.stock_service.get_quote", lambda symbol: {"symbol": symbol, "currency": "USD", "interval": "1Min", "source": "alpaca", "points": [{"timestamp": "2026-02-14T00:00:00+00:00", "price": 100.0}]})
    response = client.get("/stocks/quote", params={"symbol": "AAPL"})
    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
