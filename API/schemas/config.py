from datetime import datetime
from pydantic import BaseModel, Field

class ConfigCreate(BaseModel):
    name: str = Field(..., max_length=64)

class ConfigResponse(BaseModel):
    name: str
    config: str
    created_at: datetime
    bytes_used: int = 0

    class Config:
        from_attributes = True

class ConfigDelete(BaseModel):
    name: str

class ConfigListResponse(BaseModel):
    configs: list[ConfigResponse]
