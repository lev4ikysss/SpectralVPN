from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr = Field(max_length=256)
    password: str = Field(min_length=6, max_length=128)
    promo_code: str | None = Field(default="", max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserTokenRevoke(BaseModel):
    token_to_revoke: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    access_token: str
    token_type: str = "bearer"
