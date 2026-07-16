from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Note, NotePriority
from app.schemas import NoteCreate, NotePatch, NoteUpdate

async def _commit_and_refresh(db: AsyncSession, note: Note) -> Note:
    try:
        await db.commit()
        await db.refresh(note)
    except SQLAlchemyError:
        await db.rollback()
        raise
    return note

async def create_note(db: AsyncSession, note_data: NoteCreate) -> Note:
    note = Note(**note_data.model_dump())
    db.add(note)
    return await _commit_and_refresh(db, note)

async def list_notes(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    priority: NotePriority | None,
    is_archived: bool | None,
) -> list[Note]:
    statement = select(Note).order_by(Note.id.desc())
    if priority is not None:
        statement = statement.where(Note.priority == priority)
    if is_archived is not None:
        statement = statement.where(Note.is_archived == is_archived)
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    result = await db.scalars(statement)
    return list(result.all())

async def get_note_by_id(db: AsyncSession, note_id: int) -> Note | None:
    result = await db.scalars(select(Note).where(Note.id == note_id))
    return result.first()

async def update_note(db: AsyncSession, note: Note, note_data: NoteUpdate) -> Note:
    for field_name, value in note_data.model_dump().items():
        setattr(note, field_name, value)
    return await _commit_and_refresh(db, note)

async def patch_note(db: AsyncSession, note: Note, note_data: NotePatch) -> Note:
    for field_name, value in note_data.model_dump(exclude_unset=True).items():
        setattr(note, field_name, value)
    return await _commit_and_refresh(db, note)

async def delete_note(db: AsyncSession, note: Note) -> None:
    try:
        await db.delete(note)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
