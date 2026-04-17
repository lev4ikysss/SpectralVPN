from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user import UserCreate, UserResponse, UserLogin, UserTokenRevoke
from models.server import Server
from models.user import User
from models.config import Config
from models.token import AuthToken
from utils.database import get_db
from utils.auth import get_password_hash, create_token, verify_password, get_current_user, hash_token
from utils.xui import XUIClient

router = APIRouter(prefix="/user")

@router.post("/signup", status_code=201)
async def signup(body: UserCreate, db: AsyncSession = Depends(get_db)):
    promo_code = (body.promo_code or "").strip()
    result = await db.execute(
        select(Server).where(
            Server.deleted_at.is_(None),
            Server.code == promo_code
        )
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(
            status_code=404,
            detail="Promo-code is not valid"
        )
    existing = await db.execute(
        select(User).where(
            User.email == body.email,
            User.deleted_at.is_(None)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Email is busy"
        )
    new_user = User(
        email=body.email,
        pass_hash= get_password_hash(body.password),
        server_id=server.id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    access_token = await create_token(user_id=new_user.id, db=db)
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        created_at=new_user.created_at,
        access_token=access_token
    )

@router.post("/login", status_code=200)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    user = result.scalar_one_or_none()
    if (not user or user.deleted_at is not None) or (not verify_password(body.password, user.pass_hash)):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    access_token = await create_token(user_id=user.id, db=db)
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        access_token=access_token
    )

@router.post("/logout", status_code=200)
async def revoke_token(body: UserTokenRevoke, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    token_to_revoke = body.token_to_revoke.strip()
    token_hash = hash_token(token_to_revoke)
    result = await db.execute(
        select(AuthToken).where(
            AuthToken.token_hash == token_hash,
            AuthToken.user_id == current_user.id
        )
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        raise HTTPException(
            status_code=404,
            detail="Token not found"
        )
    if token_record.revoked:
        return {"message": "Token already revoked"}
    token_record.revoked = True
    token_record.revoked_at = datetime.utcnow()
    await db.commit()
    return {"message": "Token successfully revoked"}

@router.delete("/delete", status_code=200)
async def delete_user(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=400,
            detail="User is already deleted"
        )
    try:
        await db.refresh(current_user, ["server"])
        server = current_user.server
        if server and server.inbound_id:
            xui = await XUIClient.from_server(server)
            result = await db.execute(
                select(Config).where(
                    Config.user_id == current_user.id,
                    Config.deleted_at.is_(None)
                )
            )
            user_configs = result.scalars().all()
            for cfg in user_configs:
                client_email_xui = f"{current_user.email}-{cfg.name}"
                try:
                    await xui.delete_client(server.inbound_id, client_email_xui)
                except:
                    pass
    except:
        pass
    current_user.deleted_at = datetime.utcnow()
    await db.execute(
        update(AuthToken)
        .where(AuthToken.user_id == current_user.id)
        .values(revoked=True, revoked_at=datetime.utcnow())
    )
    await db.execute(
        update(Config)
        .where(Config.user_id == current_user.id, Config.deleted_at.is_(None))
        .values(deleted_at=datetime.utcnow())
    )
    await db.commit()
    return {"message": "User has been successfully deleted"}
