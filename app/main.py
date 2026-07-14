from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Query

from app.schemas import NoteCreate

app = FastAPI(
    title="Python Intern Day 1-2 Sandbox",
    version="0.1.0",
    description="验证 Pydantic v2、FastAPI 路由、依赖注入、异步函数和 /docs。",
)


async def list_parameters(
    q: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=10, ge=1, le=100),
) -> dict[str, str | int | None]:
    return {"q": q, "limit": limit}


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/notes", tags=["notes"])
async def list_notes(
    params: Annotated[dict[str, str | int | None], Depends(list_parameters)],
) -> dict[str, object]:
    return {
        "message": "Day 2 示例接口，尚未连接正式 Note 表",
        "filters": params,
        "items": [],
    }


@app.post("/notes/preview", response_model=NoteCreate, tags=["notes"])
async def preview_note(payload: NoteCreate) -> NoteCreate:
    return payload
