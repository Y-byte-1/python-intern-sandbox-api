from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import NotePriority


Title = Annotated[
    str,
    Field(min_length=1, max_length=100),
]

Content = Annotated[
    str | None,
    Field(max_length=10000),
]

Tag = Annotated[
    str,
    Field(min_length=1, max_length=20),
]


class NoteBase(BaseModel):
    """Note 公共字段。"""

    model_config = ConfigDict(extra="forbid")

    title: Title
    content: Content = None
    priority: NotePriority = NotePriority.medium
    tags: list[Tag] = Field(default_factory=list, max_length=5)
    is_archived: bool = False

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: Any) -> Any:
        """清理标题，并禁止出现尖括号。"""

        if isinstance(value, str):
            value = value.strip()

            if "<" in value or ">" in value:
                raise ValueError("title 不能包含特殊字符 < 或 >")

        return value

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value: Any) -> Any:
        """清理标签，并禁止标签重复。"""

        if value is None or not isinstance(value, list):
            return value

        if not all(isinstance(item, str) for item in value):
            return value

        cleaned_tags = [item.strip() for item in value]
        normalized_tags = [item.casefold() for item in cleaned_tags]

        if len(normalized_tags) != len(set(normalized_tags)):
            raise ValueError("tags 不能重复")

        return cleaned_tags


class NoteCreate(NoteBase):
    """POST 创建便签时使用。"""


class NoteUpdate(NoteBase):
    """PUT 全量更新时使用，所有字段必须明确传入。"""

    content: Content
    priority: NotePriority
    tags: list[Tag] = Field(max_length=5)
    is_archived: bool


class NotePatch(NoteBase):
    """PATCH 部分更新时使用，所有字段均可不传。"""

    title: Title | None = None
    content: Content = None
    priority: NotePriority | None = None
    tags: list[Tag] | None = Field(default=None, max_length=5)
    is_archived: bool | None = None


class NoteOut(NoteBase):
    """接口返回便签数据时使用。"""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: int
    created_at: datetime
    updated_at: datetime