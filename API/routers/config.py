from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.user import User
from models.config import Config
from schemas.config import ConfigCreate, ConfigResponse, ConfigListResponse, ConfigDelete
from utils.auth import get_current_user
from utils.database import get_db
from utils.xui import XUIClient

router = APIRouter(prefix="/config")

@router.post("/add", status_code=201)
async def create_config(body: ConfigCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Config).where(
            Config.user_id == current_user.id,
            Config.name == body.name,
            Config.deleted_at.is_(None)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Config name is invalid"
        )
    result = await db.execute(
        select(User)
        .where(User.id == current_user.id)
        .options(selectinload(User.server))
    )
    user_with_server = result.scalar_one()
    server = user_with_server.server
    if not server or server.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="The server not found"
        )
    xui = await XUIClient.from_server(server)
    client_email_xui = f"{current_user.email}-{body.name}"
    display_name = f"SpectralVPN-{body.name}"
    config_url = await xui.add_client(
        client_email=client_email_xui,
        display_name=display_name
    )
    new_config = Config(
        user_id=current_user.id,
        name=body.name,
        config=config_url
    )
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    return ConfigResponse(
        name=new_config.name,
        config=new_config.config,
        created_at=new_config.created_at,
        bytes_used=0
    )

@router.get("/get_info")
async def get_configs(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Config).where(
            Config.user_id == current_user.id,
            Config.deleted_at.is_(None)
        ).order_by(Config.created_at.desc())
    )
    configs_db = result.scalars().all()
    configs = []
    xui = None
    for cfg in configs_db:
        bytes_used = 0
        try:
            if xui is None:
                server_result = await db.execute(
                    select(User)
                    .where(User.id == current_user.id)
                    .options(selectinload(User.server))
                )
                server = server_result.scalar_one().server
                xui = await XUIClient.from_server(server)
            client_email = f"{current_user.email}-{cfg.name}"
            bytes_used = await xui.get_client_traffic(client_email)
        except:
            pass
        configs.append(
            ConfigResponse(
                name=cfg.name,
                config=cfg.config,
                created_at=cfg.created_at,
                bytes_used=bytes_used
            )
        )
    return ConfigListResponse(configs=configs)

@router.delete("/delete", status_code=204)
async def delete_config(body: ConfigDelete, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Config).where(
            Config.user_id == current_user.id,
            Config.name == body.name,
            Config.deleted_at.is_(None)
        )
    )
    config_record = result.scalar_one_or_none()
    if not config_record:
        raise HTTPException(
            status_code=404,
            detail="Config not found"
        )
    try:
        server_result = await db.execute(
            select(User)
            .where(User.id == current_user.id)
            .options(selectinload(User.server))
        )
        server = server_result.scalar_one().server
        if server:
            xui = await XUIClient.from_server(server)
            client_email_xui = f"{current_user.email}-{body.name}"
            await xui.delete_client(client_email_xui)
    except:
        HTTPException(
            status_code=500,
            detail="Server error"
        )
    config_record.deleted_at = datetime.utcnow()
    await db.commit()
    return None
