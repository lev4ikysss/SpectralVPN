from datetime import datetime
from pydantic import BaseModel, Field

class ServerBase(BaseModel):
    name: str = Field(max_length=64)
    user: str = Field(max_length=64)
    password: str = Field(max_length=64)

class ServerAdd(ServerBase):
    port: int = Field(ge=1, le=65536)
    code: str = Field(max_length=128)
    inbound_id: int

class ServerDel(ServerBase):
    pass

class ServerInfo(BaseModel):
    id: int
    name: str = Field(max_length=64)
    code: str
    created_at: datetime
