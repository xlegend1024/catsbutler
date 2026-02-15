from datetime import datetime

from pydantic import BaseModel

from .chat import ChatMessage


class ConversationSummary(BaseModel):
    id: str
    title: str
    updatedAt: datetime


class ConversationRecord(BaseModel):
    id: str
    title: str
    createdAt: datetime
    updatedAt: datetime
    messages: list[ChatMessage]
