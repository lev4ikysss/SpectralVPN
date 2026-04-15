from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.server import Server
from schemas.server import ServerAdd, ServerDel, ServerInfo
from utils.database import get_db

router = APIRouter(prefix="/server")

@router.post("/add", status_code=201)
async def add_server(body: ServerAdd, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host
    existing = await db.execute(
        select(Server).where(
            (Server.name == body.name) |
            (Server.code == body.code) |
            (Server.host == ip)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Name, ip or code is already exists"
        )
    new_server = Server(
        name=body.name,
        code=body.code,
        host=ip,
        port=body.port,
        user=body.user,
        password=body.password,
        inbound_id=body.inbound_id
    )
    db.add(new_server)
    await db.commit()
    await db.refresh(new_server)
    return ServerInfo.model_validate(new_server, from_attributes=True)

@router.delete("/delete", status_code=204)
async def del_server(body: ServerDel, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Server).where(
            (Server.name == body.name) &
            (Server.user == body.user) &
            (Server.password == body.password) &
            (Server.deleted_at.is_(None))
        )
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(
            status_code=404,
            detail="Server not found, or invalid secure_key"
        )
    server.deleted_at = datetime.utcnow()
    await db.commit()
    return None