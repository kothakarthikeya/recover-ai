from pydantic import BaseModel
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    database_status: str
    timestamp: datetime
