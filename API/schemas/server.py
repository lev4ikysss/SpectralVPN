from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class ServerBase(BaseModel):
    name: str = Field(max_length=64)
    user: str = Field(max_length=64)
    password: str = Field(max_length=64)

class ServerAdd(ServerBase):
    host: str = Field(max_length=128)
    port: int = Field(ge=1, le=65536)
    code: str = Field(max_length=128)
    inbound_id: int
    version: Literal["legacy", "stable"]

class ServerDel(ServerBase):
    pass

class ServerInfo(BaseModel):
    id: int
    name: str = Field(max_length=64)
    code: str
    created_at: datetime
    version: str
