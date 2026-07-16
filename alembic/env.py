"""
这是第四部分修改的，前面配置了环境，建立了数据库连接database，增加了Note模型schema
models.py 只是 Python 中的表结构，还没有真正创建 PostgreSQL 数据表。
所以接下来配置 Alembic。
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 导入项目数据库基类与连接地址；导入全部 ORM 模型（副作用导入）
# 只有导入模型类，它们才会注册到 Base.metadata 中，Alembic 才能检测到表结构变化
# noqa: F401 忽略「导入未使用」的代码检查告警，该导入为必要副作用
from app.database import Base, DATABASE_URL
from app import models  # noqa: F401


# 获取 Alembic 配置对象，对应 alembic.ini 配置文件的解析结果
config = context.config

# 用代码中统一维护的数据库地址，覆盖配置文件里的 sqlalchemy.url
# 避免配置文件与业务代码各维护一份地址，出现不一致
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL,
)

# 若配置文件指定了日志配置文件，则加载对应日志设置，控制迁移过程的日志输出
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 指定迁移对比的目标元数据：所有 ORM 模型的表结构都汇总在 Base.metadata
# Alembic 以此为基准，与数据库真实表结构对比，自动生成差异迁移脚本
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线生成迁移 SQL。"""
    # 离线模式：不连接真实数据库，直接生成可独立执行的 SQL 脚本
    # 用于生产环境需人工审核 SQL、无数据库直连权限的场景

    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,  # 开启字段类型对比，可检测字段类型/长度变更并生成迁移
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(
    connection: Connection,
) -> None:
    # 迁移执行的核心同步逻辑
    # Alembic 原生迁移逻辑为同步实现，异步模式下通过 run_sync 桥接调用该函数
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # 开启字段类型对比，与离线模式行为保持一致
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # 异步在线迁移的核心包装函数
    # 基于异步引擎建立数据库连接，再桥接同步的迁移执行逻辑

    # 从配置文件中读取 sqlalchemy 相关配置段
    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    # 创建异步数据库引擎
    # 迁移为一次性短连接操作，使用 NullPool 禁用连接池，执行完直接释放连接
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # 建立异步数据库连接
    async with connectable.connect() as connection:
        # 异步转同步桥接：在异步连接上同步执行迁移核心逻辑
        await connection.run_sync(do_run_migrations)

    # 迁移完成，销毁引擎、释放全部数据库资源
    await connectable.dispose()


def run_migrations_online() -> None:
    # 在线模式入口：直接连接数据库并执行迁移脚本
    # 开发/测试环境执行 alembic upgrade head 时默认走该流程
    asyncio.run(run_async_migrations())


# 主入口：根据执行命令自动选择运行模式
# 离线模式（如加 --sql 参数生成 SQL）走离线分支，普通执行走在线分支
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
