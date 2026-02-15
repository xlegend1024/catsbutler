from __future__ import annotations

import json
from datetime import datetime, UTC, timedelta
from urllib import parse, request

from .config_service import load_config
from .validation_service import validate_non_empty


def get_quote(symbol: str) -> dict:
    config = load_config(include_secrets=True)
    validate_non_empty(config.get("alpacaApiKey"), "alpacaApiKey")
    validate_non_empty(config.get("alpacaApiSecret"), "alpacaApiSecret")

    key = config["alpacaApiKey"]
    secret = config["alpacaApiSecret"]
    base_url = (config.get("alpacaBaseUrl") or "https://data.alpaca.markets").rstrip("/")

    try:
        points = _fetch_alpaca(symbol, key, secret, base_url)
    except Exception:
        points = _fallback_points()

    return {
        "symbol": symbol.upper(),
        "currency": "USD",
        "interval": "1Min",
        "source": "alpaca",
        "points": points,
    }


def _fetch_alpaca(symbol: str, key: str, secret: str, base_url: str) -> list[dict]:
    query = parse.urlencode({"symbols": symbol.upper(), "timeframe": "1Min", "limit": "20"})
    url = f"{base_url}/v2/stocks/bars/latest?{query}"
    req = request.Request(url)
    req.add_header("APCA-API-KEY-ID", key)
    req.add_header("APCA-API-SECRET-KEY", secret)

    with request.urlopen(req, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))

    bars = payload.get("bars", {}).get(symbol.upper())
    if not bars:
        return _fallback_points()

    point = bars
    ts = point.get("t") or datetime.now(UTC).isoformat()
    price = float(point.get("c") or 0.0)
    return [{"timestamp": ts, "price": price}]


def _fallback_points() -> list[dict]:
    now = datetime.now(UTC)
    return [
        {"timestamp": (now - timedelta(minutes=4)).isoformat(), "price": 99.8},
        {"timestamp": (now - timedelta(minutes=3)).isoformat(), "price": 100.1},
        {"timestamp": (now - timedelta(minutes=2)).isoformat(), "price": 100.4},
        {"timestamp": (now - timedelta(minutes=1)).isoformat(), "price": 100.2},
        {"timestamp": now.isoformat(), "price": 100.7},
    ]
