from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_note, delete_note, get_note_by_id, list_notes, patch_note, update_note
from app.database import get_db
from app.exceptions import NoteNotFoundError
from app.models import NotePriority
from app.schemas import ErrorResponse, NoteCreate, NoteOut, NotePatch, NoteUpdate

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)

DbSession = Annotated[AsyncSession, Depends(get_db)]
NoteId = Annotated[int, Path(ge=1, description="Note ID，必须大于等于 1")]

@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note_endpoint(payload: NoteCreate, db: DbSession) -> NoteOut:
    return NoteOut.model_validate(await create_note(db, payload))

@router.get("", response_model=list[NoteOut])
async def list_notes_endpoint(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    priority: NotePriority | None = None,
    is_archived: bool | None = None,
) -> list[NoteOut]:
    notes = await list_notes(
        db,
        page=page,
        page_size=page_size,
        priority=priority,
        is_archived=is_archived,
    )
    return [NoteOut.model_validate(note) for note in notes]

@router.get("/{note_id}", response_model=NoteOut, responses={404: {"model": ErrorResponse}})
async def get_note_endpoint(note_id: NoteId, db: DbSession) -> NoteOut:
    note = await get_note_by_id(db, note_id)
    if note is None:
        raise NoteNotFoundError()
    return NoteOut.model_validate(note)

@router.put("/{note_id}", response_model=NoteOut, responses={404: {"model": ErrorResponse}})
async def update_note_endpoint(
    note_id: NoteId,
    payload: NoteUpdate,
    db: DbSession,
) -> NoteOut:
    note = await get_note_by_id(db, note_id)
    if note is None:
        raise NoteNotFoundError()
    return NoteOut.model_validate(await update_note(db, note, payload))

@router.patch("/{note_id}", response_model=NoteOut, responses={404: {"model": ErrorResponse}})
async def patch_note_endpoint(
    note_id: NoteId,
    payload: NotePatch,
    db: DbSession,
) -> NoteOut:
    note = await get_note_by_id(db, note_id)
    if note is None:
        raise NoteNotFoundError()
    return NoteOut.model_validate(await patch_note(db, note, payload))

@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={404: {"model": ErrorResponse}},
)
async def delete_note_endpoint(note_id: NoteId, db: DbSession) -> Response:
    note = await get_note_by_id(db, note_id)
    if note is None:
        raise NoteNotFoundError()
    await delete_note(db, note)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
