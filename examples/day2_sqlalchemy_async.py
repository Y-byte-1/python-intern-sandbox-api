from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.database import Base, DemoNote, SessionFactory, engine


async def reset_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def insert_note() -> None:
    async with SessionFactory.begin() as session:
        session.add(DemoNote(title="SQLAlchemy 2.0 async 示例"))


async def query_notes() -> list[DemoNote]:
    async with SessionFactory() as session:
        result = await session.scalars(select(DemoNote).order_by(DemoNote.id))
        return list(result)


async def main() -> None:
    await reset_tables()
    await insert_note()
    notes = await query_notes()

    for note in notes:
        print(
            {
                "id": note.id,
                "title": note.title,
                "created_at": note.created_at,
            }
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
