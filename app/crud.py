from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Note, NotePriority
from app.schemas import NoteCreate


async def create_note(
    db: AsyncSession,
    note_data: NoteCreate,
) -> Note:
    """创建一条便签。"""

    note = Note(**note_data.model_dump())

    db.add(note)
    await db.commit()
    await db.refresh(note)

    return note


async def list_notes(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    priority: NotePriority | None,
    is_archived: bool | None,
) -> list[Note]:
    """分页查询便签，并支持优先级和归档状态筛选。"""

    statement = select(Note).order_by(Note.id.desc())

    if priority is not None:
        statement = statement.where(Note.priority == priority)

    if is_archived is not None:
        statement = statement.where(Note.is_archived == is_archived)

    statement = statement.offset(
        (page - 1) * page_size
    ).limit(page_size)

    result = await db.scalars(statement)

    return list(result.all())


async def get_note_by_id(
    db: AsyncSession,
    note_id: int,
) -> Note | None:
    """按 ID 查询一条便签。"""

    statement = select(Note).where(Note.id == note_id)
    result = await db.scalars(statement)

    return result.first()