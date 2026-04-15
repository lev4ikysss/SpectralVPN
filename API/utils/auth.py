import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from models.token import AuthToken
from models.user import User
from utils.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"])
API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=False)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

async def create_token(user_id: int, db: AsyncSession) -> str:
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_token(raw_token)
    new_token = AuthToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(new_token)
    await db.commit()
    await db.refresh(new_token)
    return raw_token

async def get_current_user(api_key: Annotated[str | None, Depends(API_KEY_HEADER)], db: AsyncSession = Depends(get_db)) -> User:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not valid"
        )
    token_hash = hash_token(api_key)
    result = await db.execute(
        select(AuthToken).where(
            AuthToken.token_hash == token_hash,
            AuthToken.revoked == False,
            AuthToken.expires_at > datetime.utcnow()
        )
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is expired"
        )
    user = await db.get(User, token_record.user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not found"
        )
    return user
