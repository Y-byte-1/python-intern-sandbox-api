# 导入 Python 标准日志模块，用于记录程序运行日志
import logging
# 导入异步迭代器类型，用于类型注解，规范 lifespan 函数的返回值类型
from collections.abc import AsyncIterator
# 导入异步上下文管理器装饰器，用于定义应用的启动和关闭逻辑
from contextlib import asynccontextmanager

# 导入 FastAPI 主应用类
from fastapi import FastAPI

# 导入数据库引擎，用于管理数据库连接池，应用关闭时需要释放连接
from app.database import engine
# 导入全局异常处理器注册函数，用于统一挂载所有自定义错误处理逻辑
from app.exceptions import register_exception_handlers
# 导入日志配置函数，用于初始化项目的日志格式、输出级别等
from app.logging_config import configure_logging
# 导入笔记模块的路由实例，并起别名为 notes_router，避免命名冲突
from app.routers.notes import router as notes_router


# 应用启动前统一执行一次日志配置，全局只需要初始化一次
# 放在模块顶层，确保应用启动时最先完成日志系统的初始化
configure_logging()

# 创建当前模块的日志记录器，名称为 app.main
# 好处：日志中可以清晰看到是哪个模块输出的日志，方便排查问题
logger = logging.getLogger(__name__)


# 异步上下文管理器装饰器，用来定义 FastAPI 应用的完整生命周期
# 分为三个阶段：启动前逻辑 -> 运行期(yield) -> 关闭后逻辑
@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """应用生命周期管理。"""

    # del app：参数 app 在此函数中没有实际使用，显式删除避免未使用变量警告
    # 生命周期函数必须接收 app 参数，但不一定非要用到
    del app

    # ===== 应用启动阶段：接收请求之前执行 =====
    # 记录应用启动日志
    logger.info("FastAPI application started")

    # yield 是生命周期的分界线：
    # yield 之前的代码在应用启动时执行
    # yield 之后的代码在应用关闭时执行
    # 应用正常运行期间，就停在 yield 这里等待接收请求
    yield

    # ===== 应用关闭阶段：停止接收请求之后执行 =====
    # 记录应用关闭日志
    logger.info("FastAPI application shutting down")

    # 释放数据库引擎的所有连接，关闭连接池，优雅退出
    await engine.dispose()


# 创建 FastAPI 应用核心实例
# title：接口文档的标题
# version：API 版本号
# lifespan：绑定上面定义的生命周期管理器，接管应用的启动和关闭流程
app = FastAPI(
    title="Python Intern Sandbox API",
    version="1.0.0",
    lifespan=lifespan,
)


# 向应用注册所有全局异常处理器
# 把自定义的 404、422、500 等错误处理逻辑挂载到 app 上，统一处理全项目的异常
register_exception_handlers(app)


# 健康检查接口：用于监控服务是否正常运行
# tags=["system"]：在接口文档中归类到 system 分组下
@app.get(
    "/health",
    tags=["system"],
)
async def health_check() -> dict[str, str]:
    """服务健康检查。"""

    # 记录健康检查被调用的日志
    logger.info("Health check requested")

    # 返回固定的健康状态，部署平台通过访问此接口判断服务是否存活
    return {
        "status": "ok",
    }


# 将笔记模块的路由注册到主应用中
# 作用：把 /notes 相关的所有接口（增删改查）挂载到主应用上，让这些接口可以被访问
app.include_router(notes_router)