import pytest
from pydantic import ValidationError

from app.models import NotePriority
from app.schemas import NoteCreate, NotePatch, NoteUpdate

def test_note_create_defaults() -> None:
    note = NoteCreate(title="学习 FastAPI")
    assert note.priority == NotePriority.medium
    assert note.tags == []
    assert note.is_archived is False
    assert note.content is None

def test_note_create_cleans_values() -> None:
    note = NoteCreate(title="  学习 FastAPI  ", tags=[" Python ", "FastAPI"])
    assert note.title == "学习 FastAPI"
    assert note.tags == ["Python", "FastAPI"]

def test_duplicate_tags_are_rejected() -> None:
    with pytest.raises(ValidationError):
        NoteCreate(title="重复标签", tags=["Python", "python"])

def test_empty_patch_is_rejected() -> None:
    with pytest.raises(ValidationError):
        NotePatch()

def test_patch_content_can_be_null() -> None:
    patch = NotePatch(content=None)
    assert patch.model_dump(exclude_unset=True) == {"content": None}

@pytest.mark.parametrize(
    "payload",
    [{"title": None}, {"priority": None}, {"tags": None}, {"is_archived": None}],
)
def test_patch_non_nullable_fields_reject_null(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        NotePatch.model_validate(payload)

def test_put_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        NoteUpdate.model_validate({"title": "缺少字段"})
