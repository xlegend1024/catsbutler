from datetime import datetime

from pydantic import BaseModel


class StockPoint(BaseModel):
    timestamp: datetime
    price: float


class StockQueryResult(BaseModel):
    symbol: str
    currency: str = "USD"
    interval: str = "1Min"
    source: str = "alpaca"
    points: list[StockPoint]


class AppConfiguration(BaseModel):
    selectedModelId: str
    autoStartService: bool = False
    maxTokens: int = 2048
    updatedAt: datetime


class AppConfigurationUpdate(BaseModel):
    selectedModelId: str
    autoStartService: bool = False
    maxTokens: int = 2048
