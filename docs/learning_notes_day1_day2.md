# Python 后端框架学习笔记（Day 1–Day 2）

## 1. 学习目标

本阶段目标是掌握 Python 后端接口开发的核心概念，其中 Pydantic 是重点；同时能够使用 FastAPI 建立异步接口，理解依赖注入与自动接口文档，并初步掌握 SQLAlchemy 2.0 的异步 ORM 写法。

---

# 2. Pydantic v2（重点）

## 2.1 Pydantic 解决什么问题

后端接口接收到的 JSON 属于外部输入，不能直接相信。Pydantic 使用 Python 类型注解描述数据结构，并完成输入解析、类型转换、字段校验、错误信息生成、序列化和 OpenAPI Schema 生成。

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
```

创建 `User(id="1", name="Tom")` 时，Pydantic 会尝试把字符串 `"1"` 转换为整数 `1`。无法转换或违反约束时，会抛出 `ValidationError`。

## 2.2 常见字段类型

```python
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl

class Profile(BaseModel):
    name: str
    age: int
    nickname: str | None = None
    skills: list[str]
    metadata: dict[str, str]
    created_at: datetime
    email: EmailStr
    homepage: HttpUrl | None = None
```

- `str`、`int`：基础类型；
- `T | None`：允许值为 None；
- `list[T]`：校验数组中每一项；
- `dict[K, V]`：校验字典键值；
- `datetime`：可从 ISO 8601 字符串解析；
- `EmailStr`：电子邮箱格式；
- `HttpUrl`：HTTP/HTTPS URL。

## 2.3 必填、可选、可空和默认值

```python
class Example(BaseModel):
    required_name: str
    nullable_but_required: str | None
    optional_with_default: str | None = None
    count: int = 0
```

`str | None` 只是“允许 None”，不一定代表调用者可以省略字段；只有提供默认值后才可不传。

PATCH Schema 中一般把可修改字段写为 `T | None = None`，再用：

```python
changes = payload.model_dump(exclude_unset=True)
```

这样只得到调用者真正传入的字段。

## 2.4 Field 字段约束

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    stock: int = Field(ge=0, le=100000)
    code: str = Field(pattern=r"^[A-Z0-9_-]+$")
```

常见参数：

- `min_length` / `max_length`
- `ge` / `le`
- `gt` / `lt`
- `default`
- `default_factory`
- `pattern`
- `description`

Pydantic v2 使用 `pattern=`；旧版常见的 `regex=` 已不再使用。

对列表和字典等可变对象，推荐：

```python
tags: list[str] = Field(default_factory=list)
```

## 2.5 field_validator

```python
from pydantic import BaseModel, field_validator

class Note(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def check_title(cls, value: str) -> str:
        if "<" in value or ">" in value:
            raise ValueError("title 不能包含尖括号")
        return value
```

注意：

1. 校验器必须返回值；
2. `mode="before"` 在类型转换前执行；
3. 默认 after 模式在字段完成类型校验后执行；
4. 能用 Field 表达的长度、范围约束优先写在 Field 中。

## 2.6 model_validator

```python
from typing import Self
from pydantic import BaseModel, model_validator

class PasswordInput(BaseModel):
    password: str
    password_repeat: str

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError("两次密码不一致")
        return self
```

当规则涉及多个字段时使用模型级校验器。

## 2.7 ConfigDict

```python
from pydantic import BaseModel, ConfigDict

class StrictInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str
```

常见配置：

- `extra="forbid"`：拒绝未声明字段；
- `str_strip_whitespace=True`：去掉首尾空格；
- `from_attributes=True`：读取普通对象或 ORM 属性；
- `validate_assignment=True`：赋值时再次校验；
- `strict=True`：严格类型模式。

## 2.8 ORM 转 Schema

```python
class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
```

随后可执行：

```python
output = NoteOut.model_validate(note_orm_object)
```

## 2.9 Schema 分离

```python
class NoteCreate(BaseModel):
    title: str

class NoteUpdate(BaseModel):
    title: str

class NotePatch(BaseModel):
    title: str | None = None

class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
```

Create 不允许客户端指定数据库生成字段；PUT 表达全量更新；PATCH 表达部分更新；Out 包含 id、created_at 等输出字段。

## 2.10 序列化与校验方法

```python
note = NoteCreate(title="A")

data = note.model_dump()
json_text = note.model_dump_json()
another = NoteCreate.model_validate({"title": "B"})
```

- `model_dump()`：模型转 Python 字典；
- `model_dump_json()`：模型转 JSON 字符串；
- `model_validate()`：字典或对象转模型；
- `model_validate_json()`：JSON 字符串/bytes 转模型。

## 2.11 ValidationError 与 FastAPI 422

普通 Python 中，校验失败抛出 `ValidationError`。FastAPI 会将请求数据校验错误默认转换为 HTTP 422，错误详情通常包含 `loc`、`msg`、`type` 和输入信息。

---

# 3. FastAPI

## 3.1 路由

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}
```

常见方法：GET、POST、PUT、PATCH、DELETE。FastAPI 根据类型注解生成 OpenAPI 文档，默认 Swagger UI 位于 `/docs`。

## 3.2 参数来源

```python
@app.get("/notes/{note_id}")
async def get_note(note_id: int):
    ...

@app.get("/notes")
async def list_notes(page: int = 1):
    ...

@app.post("/notes")
async def create_note(payload: NoteCreate):
    ...
```

分别对应路径参数、查询参数和 JSON 请求体。

## 3.3 Depends

依赖注入用于复用数据库 Session、登录用户、分页参数、权限检查和配置读取。

```python
from typing import Annotated
from fastapi import Depends

async def get_common():
    return {"limit": 10}

@app.get("/items")
async def items(common: Annotated[dict, Depends(get_common)]):
    return common
```

## 3.4 async def

适合异步数据库访问、HTTP 请求、消息系统等 I/O 等待场景。异步不等于多线程，也不适合直接解决 CPU 密集计算。

---

# 4. SQLAlchemy 2.0 async ORM

核心对象：

- `create_async_engine()`
- `async_sessionmaker()`
- `AsyncSession`
- `DeclarativeBase`
- `Mapped` / `mapped_column`
- `select()`

```python
engine = create_async_engine(DATABASE_URL)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)
```

查询：

```python
async with SessionFactory() as session:
    result = await session.scalars(select(Note))
    notes = list(result)
```

写操作通常放在事务中：

```python
async with SessionFactory.begin() as session:
    session.add(note)
```

正式项目中的数据库结构变更应交给 Alembic 迁移。

---

# 5. 前后端分离与微服务

前后端分离：前端负责页面与交互，后端通过 HTTP API 提供业务数据，双方通过请求和响应 Schema 协作。

微服务：按业务域拆分用户、订单、内容、通知等独立服务。拆分会增加网络调用、失败重试、分布式事务、日志追踪、配置和部署复杂度，不能为了形式随意拆分。

---

# 6. 自测问题

1. `str | None` 为什么不一定代表字段可以省略？
2. `Field` 和 `field_validator` 如何分工？
3. 为什么 PATCH 使用 `exclude_unset=True`？
4. `model_dump()` 与 `model_validate()` 的方向是什么？
5. `from_attributes=True` 解决什么问题？
6. FastAPI 为什么能生成 `/docs`？
7. `Depends` 常用于哪些场景？
8. `async def` 适合和不适合什么任务？
9. Engine、SessionFactory、AsyncSession 分别是什么？
10. 为什么数据库表变更需要 Alembic？
