from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from utils.database import engine
import models
from routers import server, user, config

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(server.router)
app.include_router(user.router)
app.include_router(config.router)

@app.get("/ping")
async def ping():
    return {"message": "pong", "time": datetime.now().timestamp()}
