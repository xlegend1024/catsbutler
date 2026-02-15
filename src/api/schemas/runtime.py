from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ServiceStatus = Literal["stopped", "starting", "running", "stopping", "error"]
ExecutionMode = Literal["NPU", "GPU", "CPU", "unknown"]
ModelAvailability = Literal["available", "downloading", "unavailable"]


class ServiceState(BaseModel):
    status: ServiceStatus
    mode: ExecutionMode = "unknown"
    activeModelId: str | None = None
    message: str | None = None
    lastUpdatedAt: datetime


class ModelProfile(BaseModel):
    id: str
    displayName: str
    availability: ModelAvailability = "available"
    recommendedMode: ExecutionMode = "unknown"


class ModelListResponse(BaseModel):
    items: list[ModelProfile]
