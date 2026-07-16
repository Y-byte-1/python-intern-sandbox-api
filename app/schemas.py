from datetime import datetime
from typing import Annotated, Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import NotePriority

Title = Annotated[str, Field(min_length=1, max_length=100)]
Content = Annotated[str | None, Field(max_length=10000)]
Tag = Annotated[str, Field(min_length=1, max_length=20)]

def clean_title(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        if "<" in value or ">" in value:
            raise ValueError("title 不能包含特殊字符 < 或 >")
    return value

def clean_tags(value: Any) -> Any:
    if value is None or not isinstance(value, list):
        return value
    if not all(isinstance(item, str) for item in value):
        return value
    cleaned = [item.strip() for item in value]
    normalized = [item.casefold() for item in cleaned]
    if len(normalized) != len(set(normalized)):
        raise ValueError("tags 不能重复")
    return cleaned

class NoteBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    content: Content = None
    priority: NotePriority = NotePriority.medium
    tags: list[Tag] = Field(default_factory=list, max_length=5)
    is_archived: bool = False

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: Any) -> Any:
        return clean_title(value)

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value: Any) -> Any:
        return clean_tags(value)

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    content: Content
    priority: NotePriority
    tags: list[Tag] = Field(max_length=5)
    is_archived: bool

class NotePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    content: Content = None
    priority: NotePriority | None = None
    tags: list[Tag] | None = Field(default=None, max_length=5)
    is_archived: bool | None = None

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: Any) -> Any:
        return clean_title(value)

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value: Any) -> Any:
        return clean_tags(value)

    @model_validator(mode="after")
    def validate_patch_body(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("PATCH 请求至少需要包含一个字段")
        for field_name in {"title", "priority", "tags", "is_archived"}:
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} 不能为 null")
        return self

class NoteOut(NoteBase):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int
    created_at: datetime
    updated_at: datetime

class ErrorDetail(BaseModel):
    field: str
    message: str
    type: str

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | dict[str, Any] | None = None
