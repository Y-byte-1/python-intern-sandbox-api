from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


Tag = Annotated[
    str,
    Field(
        min_length=1,
        max_length=20,
        pattern=r"^[^<>]+$",
        description="单个标签长度为 1-20，且不能包含尖括号",
    ),
]


class NoteBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[^<>]+$",
        description="标题必填，1-100 字，不能包含 < 或 >",
    )
    content: str | None = Field(default=None, max_length=10_000)
    priority: Priority = Priority.medium
    tags: list[Tag] = Field(default_factory=list, max_length=5)
    is_archived: bool = False

    metadata: dict[str, str] = Field(default_factory=dict)
    owner_email: EmailStr | None = None
    reference_url: HttpUrl | None = None
    due_at: datetime | None = None

    @field_validator("tags")
    @classmethod
    def tags_must_be_unique(cls, value: list[str]) -> list[str]:
        normalized = [tag.strip().lower() for tag in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("tags 不能重复")
        return normalized

    @model_validator(mode="after")
    def title_and_content_must_differ(self) -> Self:
        if self.content and self.title == self.content.strip():
            raise ValueError("title 与 content 不能完全相同")
        return self


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class NotePatch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[^<>]+$",
    )
    content: str | None = Field(default=None, max_length=10_000)
    priority: Priority | None = None
    tags: list[Tag] | None = Field(default=None, max_length=5)
    is_archived: bool | None = None
    metadata: dict[str, str] | None = None
    owner_email: EmailStr | None = None
    reference_url: HttpUrl | None = None
    due_at: datetime | None = None

    @field_validator("tags")
    @classmethod
    def tags_must_be_unique(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = [tag.strip().lower() for tag in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("tags 不能重复")
        return normalized


class NoteOut(NoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
