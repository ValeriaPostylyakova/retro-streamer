from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models
from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.redis_client import redis_async_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_async_client.ping()
    print("Connected to Redis")
    yield
    await redis_async_client.close()


app = FastAPI(
    title="Retro-Streamer",
    version="1.0.0",
    description="Backend-сервис для запуска ретро-игр, асинхронной генерации GIF-прохождений и публикации результатов в таблице лидеров.",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

app.include_router(api_router, prefix="/api/v1")


origins = [
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, exc: ApplicationError):
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers
    )
