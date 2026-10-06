from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.ping()
    print("Connected to Redis")
    yield
    await redis_client.close()


app = FastAPI(title="fastapi_task_manager", lifespan=lifespan, debug=settings.DEBUG)


def get_current_user():
    return {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
    }
