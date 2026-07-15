from fastapi import FastAPI

from app.routers.notes import router as notes_router


app = FastAPI(
    title="Python Intern Sandbox API",
    version="1.0.0",
)


@app.get(
    "/health",
    tags=["system"],
)
async def health_check() -> dict[str, str]:
    """服务健康检查。"""

    return {
        "status": "ok",
    }


app.include_router(notes_router)