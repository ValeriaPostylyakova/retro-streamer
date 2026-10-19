from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models
from app.api.v1 import api_router
from app.core.config import settings
from app.core.redis_client import redis_async_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_async_client.ping()
    print("Connected to Redis")
    yield
    await redis_async_client.close()


app = FastAPI(title="fastapi_task_manager", lifespan=lifespan, debug=settings.DEBUG)

app.include_router(api_router, prefix="/api/v1")
