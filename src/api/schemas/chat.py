from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ChatRole = Literal["user", "assistant", "system", "tool"]


class ChartPoint(BaseModel):
    timestamp: datetime
    price: float


class ChartPayload(BaseModel):
    type: Literal["line"] = "line"
    points: list[ChartPoint]


class ChatMessage(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    conversationId: str | None = None


class ChatResponse(BaseModel):
    reply: str
    chart: ChartPayload | None = None
    conversationId: str | None = None
