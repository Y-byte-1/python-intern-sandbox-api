from __future__ import annotations

from datetime import UTC, datetime

from pydantic import ValidationError

from app.schemas import NoteCreate, NoteOut, NotePatch


def print_title(text: str) -> None:
    print("\n" + "=" * 18 + f" {text} " + "=" * 18)


def valid_examples() -> None:
    print_title("1. BaseModel + 字段类型 + Field 约束")

    note = NoteCreate(
        title="学习 Pydantic v2",
        content="练习 BaseModel、Field 和自定义校验器",
        priority="high",
        tags=["Python", "Pydantic"],
        metadata={"source": "intern-task"},
        owner_email="student@example.com",
        reference_url="https://example.com/pydantic",
        due_at="2026-07-15T18:00:00+08:00",
    )
    print(note)

    print_title("2. model_dump")
    print(note.model_dump())

    print_title("3. model_dump_json")
    print(note.model_dump_json(indent=2))

    print_title("4. model_validate")
    note_from_dict = NoteCreate.model_validate(
        {
            "title": "从字典校验",
            "priority": "medium",
            "tags": ["schema"],
        }
    )
    print(note_from_dict)

    print_title("5. PATCH + exclude_unset")
    patch = NotePatch.model_validate({"priority": "low"})
    print("完整 dump:", patch.model_dump())
    print("只保留实际传入字段:", patch.model_dump(exclude_unset=True))


class FakeOrmNote:
    id = 1
    title = "ORM 转 Schema"
    content = None
    priority = "medium"
    tags = ["orm", "schema"]
    is_archived = False
    metadata: dict[str, str] = {}
    owner_email = None
    reference_url = None
    due_at = None
    created_at = datetime.now(UTC)
    updated_at = datetime.now(UTC)


def orm_example() -> None:
    print_title("6. from_attributes=True")
    output = NoteOut.model_validate(FakeOrmNote())
    print(output.model_dump())


def invalid_examples() -> None:
    cases = [
        {"name": "标题包含尖括号", "data": {"title": "<script>", "tags": []}},
        {
            "name": "标签超过 5 个",
            "data": {"title": "标签太多", "tags": ["a", "b", "c", "d", "e", "f"]},
        },
        {
            "name": "标签重复（忽略大小写）",
            "data": {"title": "重复标签", "tags": ["Python", "python"]},
        },
        {
            "name": "标题与内容完全相同",
            "data": {"title": "相同", "content": "相同"},
        },
        {
            "name": "出现未声明字段",
            "data": {"title": "额外字段", "unknown": 123},
        },
    ]

    print_title("7. ValidationError")
    for case in cases:
        try:
            NoteCreate.model_validate(case["data"])
        except ValidationError as exc:
            print(f"\n[{case['name']}]")
            for error in exc.errors():
                print(
                    {
                        "type": error["type"],
                        "loc": error["loc"],
                        "msg": error["msg"],
                    }
                )


if __name__ == "__main__":
    valid_examples()
    orm_example()
    invalid_examples()
