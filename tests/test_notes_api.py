"""Note API 集成测试。测试使用独立 PostgreSQL 数据库 intern_test_db。"""

from collections.abc import AsyncGenerator
from typing import TypedDict, Unpack

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

pytestmark = pytest.mark.anyio

TEST_DATABASE_NAME = "intern_test_db"
TEST_DATABASE_URL = (
    "postgresql+asyncpg://intern:intern_password@127.0.0.1:5432/" f"{TEST_DATABASE_NAME}"
)

ADMIN_DATABASE_CONFIG = {
    "user": "intern",
    "password": "intern_password",
    "host": "127.0.0.1",
    "port": 5432,
    "database": "postgres",
}

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


async def ensure_test_database_exists() -> None:
    connection = await asyncpg.connect(**ADMIN_DATABASE_CONFIG)
    try:
        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            TEST_DATABASE_NAME,
        )
        if not exists:
            await connection.execute(f'CREATE DATABASE "{TEST_DATABASE_NAME}"')
    finally:
        await connection.close()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(scope="session", autouse=True)
async def prepare_test_database() -> AsyncGenerator[None, None]:
    await ensure_test_database_exists()

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture(autouse=True)
async def clean_notes_table(
    prepare_test_database: None,
) -> AsyncGenerator[None, None]:
    del prepare_test_database

    async with test_engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE notes RESTART IDENTITY CASCADE"))

    yield

    async with test_engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE notes RESTART IDENTITY CASCADE"))


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        yield test_client


class NotePayloadOverrides(TypedDict, total=False):
    """测试辅助函数允许覆盖的 Note 请求字段。"""

    title: str
    content: str | None
    priority: str
    tags: list[str] | None
    is_archived: bool


def build_note_payload(
    *,
    title: str = "学习 FastAPI",
    content: str | None = "完成 Note CRUD 接口",
    priority: str = "high",
    tags: list[str] | None = None,
    is_archived: bool = False,
) -> dict[str, object]:
    return {
        "title": title,
        "content": content,
        "priority": priority,
        "tags": tags if tags is not None else ["python", "fastapi"],
        "is_archived": is_archived,
    }


async def create_note_for_test(
    client: AsyncClient,
    **overrides: Unpack[NotePayloadOverrides],
) -> dict[str, object]:
    response = await client.post(
        "/notes",
        json=build_note_payload(**overrides),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_post_create_success(client: AsyncClient) -> None:
    response = await client.post("/notes", json=build_note_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "学习 FastAPI"
    assert body["content"] == "完成 Note CRUD 接口"
    assert body["priority"] == "high"
    assert body["tags"] == ["python", "fastapi"]
    assert body["is_archived"] is False
    assert body["created_at"]
    assert body["updated_at"]


async def test_get_list_success(client: AsyncClient) -> None:
    first = await create_note_for_test(
        client,
        title="第一条 Note",
        priority="medium",
        tags=["first"],
    )
    second = await create_note_for_test(
        client,
        title="第二条 Note",
        priority="high",
        tags=["second"],
    )

    response = await client.get("/notes", params={"page": 1, "page_size": 20})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["id"] == second["id"]
    assert body[1]["id"] == first["id"]


async def test_get_detail_success(client: AsyncClient) -> None:
    created = await create_note_for_test(client)
    response = await client.get(f"/notes/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


async def test_get_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get("/notes/999")

    assert response.status_code == 404
    assert response.json() == {
        "code": "NOTE_NOT_FOUND",
        "message": "Note not found",
        "details": None,
    }


async def test_put_complete_update_success(client: AsyncClient) -> None:
    created = await create_note_for_test(client)
    payload = build_note_payload(
        title="完整更新后的标题",
        content="完整更新后的内容",
        priority="medium",
        tags=["python", "update"],
        is_archived=True,
    )

    response = await client.put(f"/notes/{created['id']}", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == "完整更新后的标题"
    assert body["content"] == "完整更新后的内容"
    assert body["priority"] == "medium"
    assert body["tags"] == ["python", "update"]
    assert body["is_archived"] is True
    assert body["created_at"] == created["created_at"]


async def test_put_missing_field_returns_422(client: AsyncClient) -> None:
    created = await create_note_for_test(client)
    payload = build_note_payload()
    payload.pop("tags")

    response = await client.put(f"/notes/{created['id']}", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed"
    assert any(item["field"] == "body.tags" for item in body["details"])


async def test_patch_partial_update_success(client: AsyncClient) -> None:
    created = await create_note_for_test(
        client,
        title="原始标题",
        content="原始内容",
        priority="medium",
        tags=["original"],
        is_archived=False,
    )

    response = await client.patch(
        f"/notes/{created['id']}",
        json={"priority": "high", "is_archived": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["priority"] == "high"
    assert body["is_archived"] is True
    assert body["title"] == created["title"]
    assert body["content"] == created["content"]
    assert body["tags"] == created["tags"]


async def test_patch_empty_body_returns_422(client: AsyncClient) -> None:
    created = await create_note_for_test(client)

    response = await client.patch(f"/notes/{created['id']}", json={})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_patch_content_null_success(client: AsyncClient) -> None:
    created = await create_note_for_test(client, content="需要清空的内容")

    response = await client.patch(
        f"/notes/{created['id']}",
        json={"content": None},
    )

    assert response.status_code == 200
    assert response.json()["content"] is None


async def test_delete_returns_204(client: AsyncClient) -> None:
    created = await create_note_for_test(client)

    response = await client.delete(f"/notes/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""


async def test_get_after_delete_returns_404(client: AsyncClient) -> None:
    created = await create_note_for_test(client)

    delete_response = await client.delete(f"/notes/{created['id']}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/notes/{created['id']}")
    assert get_response.status_code == 404
    assert get_response.json()["code"] == "NOTE_NOT_FOUND"


async def test_database_error_returns_unified_500(
    client: AsyncClient,
) -> None:
    async def broken_get_db() -> AsyncGenerator[AsyncSession, None]:
        raise SQLAlchemyError("forced test database error")
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = broken_get_db

    try:
        response = await client.get("/notes")
    finally:
        app.dependency_overrides[get_db] = override_get_db

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "Internal server error",
        "details": None,
    }
    assert "forced test database error" not in response.text
