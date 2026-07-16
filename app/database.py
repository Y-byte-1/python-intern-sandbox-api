import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


# ------------------------------
# 1. 数据库连接配置
# ------------------------------
# 从环境变量读取数据库连接地址，若未配置则使用本地默认值
# 连接串格式： dialect+driver://用户名:密码@主机:端口/数据库名
# postgresql+asyncpg：表示使用 PostgreSQL 数据库，搭配 asyncpg 异步驱动
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://intern:intern_password@127.0.0.1:5432/intern_db",
)


# ------------------------------
# 2. ORM 模型基类
# ------------------------------
# 所有自定义数据表模型都必须继承这个基类
# DeclarativeBase 是 SQLAlchemy 2.0 声明式映射的核心基类，支持 Mapped + mapped_column 类型化写法
# 后续创建表、迁移表结构都依赖这个基类统一管理所有模型
class Base(DeclarativeBase):
    """所有 SQLAlchemy ORM 数据表模型的公共基类。"""


# ------------------------------
# 3. 异步数据库引擎（Engine）
# ------------------------------
# engine 是数据库连接的核心底层对象，负责管理数据库连接池、SQL 编译与执行
# 整个应用全局只需要创建一个 engine 实例，所有会话都复用这个引擎的连接池
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # 是否打印执行的 SQL 语句，开发调试可设为 True，生产环境关闭
    pool_pre_ping=True,  # 连接池健康检查：每次从池中取连接前，先测试连接是否还存活
                         # 避免数据库主动断开连接后，程序拿到失效连接报错
)


# ------------------------------
# 4. 异步会话工厂（Session Factory）
# ------------------------------
# async_sessionmaker 是会话的「工厂类」，用来批量生成会话对象
# 不直接全局共享一个 Session，因为 Session 不是线程/协程安全的，每个请求必须用独立的 Session
AsyncSessionLocal = async_sessionmaker(
    bind=engine,                # 绑定上面创建的数据库引擎，复用连接池
    class_=AsyncSession,        # 指定生成的会话类型为异步会话
    expire_on_commit=False,     # 提交事务后，不将会话内的对象标记为「过期」
                                # 设为 False 后，提交事务后依然可以直接读取对象属性，无需重新查询
                                # 配合 FastAPI 接口返回数据非常常用，避免提交后访问属性触发额外查询
)


# ------------------------------
# 5. 数据库会话依赖（FastAPI 依赖注入用）
# ------------------------------
# 这是 FastAPI 标准的依赖注入函数，每个请求进来时自动创建一个新 Session
# 请求处理完成后自动关闭 Session，遇到异常自动回滚事务
# 返回类型 AsyncGenerator[AsyncSession, None]：异步生成器，产出一个 AsyncSession，不接收回传值
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖：为每个 HTTP 请求提供独立的数据库会话。
    - 正常执行：yield 将会话注入到接口函数中，请求结束后自动关闭会话
    - 发生异常：自动执行事务回滚，保证数据一致性，随后重新抛出异常交给全局异常处理器
    """
    # async with 上下文管理：自动管理会话的打开与关闭，用完自动归还连接到连接池
    async with AsyncSessionLocal() as session:
        try:
            # yield 将当前会话「交出去」给调用方（接口函数）使用
            # 代码会暂停在这里，直到接口函数执行完毕后再继续往下走
            yield session
        except Exception:
            # 接口执行过程中出现任何异常，先回滚当前事务，避免脏数据留在会话中
            await session.rollback()
            # 回滚后重新抛出异常，交给 FastAPI 全局异常处理器统一处理返回
            raise