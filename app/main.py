import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.routers.notes import router as notes_router

# 应用启动时统一配置一次日志。
configure_logging()

# 当前 Logger 名称为 app.main。
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """应用生命周期管理。"""

    del app

    logger.info("FastAPI application started")

    yield

    logger.info("FastAPI application shutting down")

    await engine.dispose()


app = FastAPI(
    title="Python Intern Sandbox API",
    version="1.0.0",
    lifespan=lifespan,
)


register_exception_handlers(app)


@app.get(
    "/health",
    tags=["system"],
)
async def health_check() -> dict[str, str]:
    """服务健康检查。"""

    logger.info("Health check requested")

    return {
        "status": "ok",
    }


app.include_router(notes_router)