"""
先定义这个是因为：
schemas.py 需要 NotePriority
crud.py 需要 Note
Alembic 需要 Base.metadata
"""

"""
### `Mapped[类型]`：Python 层面的类型标记

`Mapped` 是 SQLAlchemy 提供的泛型类型，作用有两个：

- 标记作用：告诉 SQLAlchemy **这个类属性是和数据库表映射的字段**
- 类型作用：方括号内指定该字段在 Python 代码中的数据类型，比如 `Mapped[int]` 表示 Python 层面操作这个字段得到的是整数

它的核心价值：

- IDE 可以精准补全属性、实时标红类型错误
- 配合 mypy 等工具实现静态类型校验
- 简单场景下，SQLAlchemy 可以根据 Python 类型**自动推断对应的数据库列类型**，不用手动指定

### 2. `mapped_column()`：数据库层面的列定义

`mapped_column()` 是真正定义「数据库表字段规则」的函数，完全等价于老版本的 `Column()`，用来指定：

- 数据库层面的列类型（`String(100)`、`Text`、`Boolean` 等）
- 列约束（主键、非空、唯一、自增等）
- 默认值、自动更新逻辑
- 索引、字段注释等属性

### 3. 两者的配合关系

一句话总结：**`Mapped` 管 Python 代码里的类型，`mapped_column` 管数据库表里的结构**。

- 简单字段：只写 `Mapped` 即可，SQLAlchemy 自动推断数据库类型
- 带约束、特殊类型的字段：`Mapped` + `mapped_column` 配合使用
"""
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, String, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
"""
所有使用 `Mapped` 写法的模型类，都必须继承自 `DeclarativeBase` 的子类，这是 SQLAlchemy 2.0 声明式模型的基础：
"""
from app.database import Base

class NotePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[NotePriority] = mapped_column(
        SqlEnum(NotePriority, name="note_priority"),
        nullable=False,
        default=NotePriority.medium,
        server_default=NotePriority.medium.value,
    )
    """
    - Python 层面：`tags` 是字符串列表 `list[str]`
    - 数据库层面：PostgreSQL 原生的一维数组类型，每个元素长度不超过 20
    - 细节说明：
    - `default=list`：Python 层面默认空列表（注意传的是 `list` 函数本身，不是 `[]`，和 Pydantic 的 `default_factory` 同理，避免所有实例共享同一个列表）
    - `server_default=text("'{}'")`：数据库层面默认空数组，`{}` 是 PostgreSQL 数组的字面量写法
    - 注意：`ARRAY` 是 PostgreSQL 专属类型，MySQL 不支持原生数组，MySQL 场景一般用 JSON 类型存储列表。
    """
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)),
        nullable=False,
        default=list,
        server_default=text("'{}'"),
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
