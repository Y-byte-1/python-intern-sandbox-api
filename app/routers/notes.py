from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_note, get_note_by_id, list_notes
from app.database import get_db
from app.models import NotePriority
from app.schemas import NoteCreate, NoteOut


router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)

DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


@router.post(
    "",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_note_endpoint(
    payload: NoteCreate,
    db: DbSession,
) -> NoteOut:
    """创建便签。"""

    note = await create_note(db, payload)
    return NoteOut.model_validate(note)


@router.get(
    "",
    response_model=list[NoteOut],
)
async def list_notes_endpoint(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    priority: NotePriority | None = None,
    is_archived: bool | None = None,
) -> list[NoteOut]:
    """分页查询便签。"""

    notes = await list_notes(
        db,
        page=page,
        page_size=page_size,
        priority=priority,
        is_archived=is_archived,
    )

    return [
        NoteOut.model_validate(note)
        for note in notes
    ]


@router.get(
    "/{note_id}",
    response_model=NoteOut,
)
async def get_note_endpoint(
    note_id: int,
    db: DbSession,
) -> NoteOut:
    """查询便签详情。"""

    note = await get_note_by_id(db, note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return NoteOut.model_validate(note)