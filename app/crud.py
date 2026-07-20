# 导入 SQLAlchemy 查询语句构造函数
from sqlalchemy import select

# 导入 SQLAlchemy 通用异常基类，用于捕获所有数据库相关异常
from sqlalchemy.exc import SQLAlchemyError

# 导入异步数据库会话类型，用于类型注解
from sqlalchemy.ext.asyncio import AsyncSession

# 导入 ORM 数据模型和优先级枚举
from app.models import Note, NotePriority

# 导入 Pydantic 入参校验模型
from app.schemas import NoteCreate, NotePatch, NoteUpdate


# 内部工具函数：提交事务并刷新 ORM 对象，异常时自动回滚
# 下划线开头为 Python 通用约定：表示该函数仅在当前模块内部使用，不对外导出
async def _commit_and_refresh(db: AsyncSession, note: Note) -> Note:
    try:
        # 提交当前事务，将会话中的所有修改真正写入数据库
        await db.commit()
        # 从数据库重新刷新对象属性，确保拿到数据库自动生成/更新的字段（如更新时间、自增ID等）
        await db.refresh(note)
    except SQLAlchemyError:
        # 数据库操作出现任何异常，回滚当前事务，避免脏数据残留在会话中
        await db.rollback()
        # 回滚后重新抛出异常，交给上层全局异常处理器统一处理
        raise
    # 返回刷新后的完整 ORM 对象
    return note


# 创建笔记：接收校验后的入参数据，写入数据库
async def create_note(db: AsyncSession, note_data: NoteCreate) -> Note:
    # 将 Pydantic 入参对象转为字典，解包后实例化 ORM 模型对象
    note = Note(**note_data.model_dump())
    # 将 ORM 对象加入当前数据库会话，标记为待插入状态
    db.add(note)
    # 调用内部工具函数完成提交、刷新并返回结果
    return await _commit_and_refresh(db, note)


# 分页条件查询笔记列表
# 参数中的 * 是 Python 强制关键字参数语法：
# 调用该函数时，* 后面的参数必须通过关键字传参，不能按位置传，避免传参顺序错误
async def list_notes(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    priority: NotePriority | None,
    is_archived: bool | None,
) -> list[Note]:
    # 构造基础查询语句：查询 Note 表，按 ID 倒序排列（最新创建的排在前面）
    statement = select(Note).order_by(Note.id.desc())
    # 动态拼接查询条件：传入了优先级参数，就追加优先级过滤条件
    if priority is not None:
        statement = statement.where(Note.priority == priority)
    # 动态拼接查询条件：传入了归档状态参数，就追加归档状态过滤条件
    if is_archived is not None:
        statement = statement.where(Note.is_archived == is_archived)
    # 分页逻辑：offset 跳过前面 N 条数据，limit 限制本次查询返回的条数
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    # 执行查询语句，scalars直接返回ORM对象流（而非原始行对象）
    result = await db.scalars(statement)
    # 取出所有查询结果，转为列表返回
    return list(result.all())


# 根据笔记ID查询单条笔记，查不到则返回 None
async def get_note_by_id(db: AsyncSession, note_id: int) -> Note | None:
    # 构造按 ID 过滤的查询语句并执行
    result = await db.scalars(select(Note).where(Note.id == note_id))
    # 取第一条结果，没有匹配数据时返回 None
    return result.first()


# 全量更新笔记（对应 PUT 请求）：用新数据覆盖对象的所有字段
async def update_note(db: AsyncSession, note: Note, note_data: NoteUpdate) -> Note:
    # 遍历入参对象的全部字段和对应值，批量赋值到已有的 ORM 对象上
    """
    这是 Python 内置函数，作用是**动态给对象设置属性值**。
    语法：`setattr(对象, 属性名字符串, 要设置的值)`
    等价于：`对象.属性名 = 要设置的值`
    """
    for field_name, value in note_data.model_dump().items():
        setattr(note, field_name, value)
    # 提交事务并刷新后返回更新后的对象
    return await _commit_and_refresh(db, note)


# 部分更新笔记（对应 PATCH 请求）：只修改用户主动传入的字段
async def patch_note(db: AsyncSession, note: Note, note_data: NotePatch) -> Note:
    # exclude_unset=True：只导出用户主动传入的字段，忽略使用默认值的字段
    # 实现「传了什么改什么，没传的保持原样」的部分更新语义
    for field_name, value in note_data.model_dump(exclude_unset=True).items():
        setattr(note, field_name, value)
    # 提交事务并刷新后返回更新后的对象
    return await _commit_and_refresh(db, note)


# 删除指定笔记
async def delete_note(db: AsyncSession, note: Note) -> None:
    try:
        # 将 ORM 对象标记为待删除状态
        await db.delete(note)
        # 提交事务，真正执行数据库删除操作
        await db.commit()
    except SQLAlchemyError:
        # 操作异常时回滚事务
        await db.rollback()
        # 重新抛出异常交由上层处理
        raise
