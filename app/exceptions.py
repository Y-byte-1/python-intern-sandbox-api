"""
全局异常处理模块。

主要职责：
1. 定义项目业务异常；
2. 将不同类型的异常转换成统一JSON响应；
3. 隐藏数据库连接、SQL、文件路径和堆栈等内部信息；
4. 在服务器日志中保留完整异常，方便排查问题；
5. 将所有异常处理器统一注册到FastAPI应用。
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)


# 获取当前模块的日志记录器。
#
# __name__ 在本文件中通常等于：
# app.exceptions
#
# 后续可以根据日志记录器名称，控制该模块的日志级别和输出位置。
logger = logging.getLogger(__name__)


class AppError(Exception):
    """
    项目业务异常的基类。

    适用于“程序能够预期并明确处理”的业务问题，例如：

    - Note 不存在；
    - 用户没有权限；
    - 资源状态不允许当前操作；
    - 数据重复；
    - 业务规则冲突。

    它和普通Exception的区别是：
    AppError中提前保存了HTTP状态码、业务错误码和客户端提示信息。

    路由层只需要：

        raise NoteNotFoundError()

    不需要在每一个接口中重复构造JSONResponse。
    """

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Any = None,
    ) -> None:
        """
        初始化业务异常。

        参数说明：
        status_code：
            HTTP 状态码，例如 404、409。

        code：
            程序使用的业务错误码，例如 NOTE_NOT_FOUND。
            前端可以根据该值执行对应逻辑。

        message：
            面向接口调用方的错误说明。

        details：
            可选的错误详情。
            可以是字典、列表或 None。
        """

        # 调用 Exception 的构造方法，
        # 这样 str(exc) 会得到 message。
        super().__init__(message)

        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class NoteNotFoundError(AppError):
    """
    Note 不存在异常。
    
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=404,
            code="NOTE_NOT_FOUND",
            message="Note not found",
            details=None,
        )


def error_body(
    *,
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    """
    构造统一错误响应体。

    所有异常最终尽量保持相同结构：

        {
            "code": "NOTE_NOT_FOUND",
            "message": "Note not found",
            "details": null
        }
    """

    return {
        "code": code,
        "message": message,
        "details": details,
    }


def log_exception(
    *,
    message: str,
    request: Request,
    exc: Exception,
) -> None:
    """
    将完整异常记录到服务器日志中。

    客户端只收到安全、简化的错误信息；
    服务器日志保留：

    - 请求路径；
    - 异常类型type(exc);
    - 异常消息(异常对象本身)exc;
    - 完整调用堆栈(exc.traceback())。

    exc_info 使用异常三元组，
    可以确保日志记录当前异常的完整traceback。
    """

    logger.error(
        "%s path=%s method=%s",
        message,
        request.url.path,
        request.method,
        exc_info=(
            type(exc), 
            exc,
            exc.__traceback__,
        ),
    )


async def app_error_handler(
    _request: Request,
    exc: AppError,
) -> JSONResponse:
    """
    处理项目主动抛出的业务异常。

    例如：

        raise NoteNotFoundError()

    最终返回：

        HTTP 404

        {
            "code": "NOTE_NOT_FOUND",
            "message": "Note not found",
            "details": null
        }

    参数名使用 _request，是因为 FastAPI 要求处理器接收 Request，
    但这个处理器当前不需要读取请求信息。
    下划线表示“参数存在，但当前未使用”。
    """

    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ),
    )


async def validation_error_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    处理请求参数校验错误。

    会进入此处理器的常见情况：

    1. 请求体字段缺失；
    2. title 长度不符合要求；
    3. priority 不属于枚举值；
    4. tags 数量超过 5 个；
    5. note_id 不是整数；
    6. note_id 小于 1；
    7. page 或 page_size 超出允许范围；
    8. Pydantic 自定义校验器失败；
    9. 请求中出现未声明字段。

    FastAPI 默认也会处理 RequestValidationError，
    这里覆盖默认处理器，是为了统一成项目自己的错误格式。
    """

    details: list[dict[str, str]] = []

    # exc.errors() 返回一个错误列表。
    # 一个请求中可能同时存在多个字段错误，因此需要逐个整理。
    for error in exc.errors():
        # loc 通常类似：
        #
        # ("body", "title")
        # ("path", "note_id")
        # ("query", "page")
        #
        # 转换后变为：
        #
        # body.title
        # path.note_id
        # query.page
        field = ".".join(
            str(item)
            for item in error.get("loc", [])
        )

        details.append(
            {
                # 错误字段位置。
                "field": field,

                # Pydantic 提供的错误说明。
                "message": str(
                    error.get(
                        "msg",
                        "Invalid value",
                    )
                ),

                # 机器可识别的校验错误类型。
                #
                # 例如：
                # missing
                # string_too_long
                # greater_than_equal
                # value_error
                "type": str(
                    error.get(
                        "type",
                        "validation_error",
                    )
                ),
            }
        )

    return JSONResponse(
        status_code=422,
        content=error_body(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
        ),
    )


async def http_error_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    处理 FastAPI 或 Starlette 产生的普通 HTTP 异常。

    常见情况：

    - 请求了不存在的路由（其实在APPerror中已经处理过了）；
    - 请求方法不允许；
    - FastAPI 内部抛出的 HTTPException；
    - 其他框架层 HTTP 错误。

    例如访问：

        GET /unknown

    可能得到：

        {
            "code": "HTTP_404",
            "message": "Not Found",
            "details": null
        }

    注意：
    此处理器主要负责框架层HTTP异常。
    """

    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            details=None,
        ),

        # 保留原异常携带的响应头。
        #
        # 某些认证异常可能包含 WWW-Authenticate 等重要响应头，
        # 自定义异常处理器时不应随意丢弃。
        headers=exc.headers,
    )


async def database_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    处理 SQLAlchemy 数据库异常。

    常见情况：

    - PostgreSQL 未启动；
    - 数据库连接中断；
    - SQL 执行失败；
    - 字段约束冲突；
    - 事务提交失败；
    - 数据库连接池异常。

    CRUD层在写操作失败时负责 rollback；
    此模块负责：

    1. 记录完整异常日志；
    2. 向客户端返回安全的统一响应；
    3. 避免泄露数据库密码、SQL、连接地址等内部信息。
    """

    log_exception(
        message="Database error",
        request=request,
        exc=exc,
    )

    return JSONResponse(
        status_code=500,
        content=error_body(
            code="DATABASE_ERROR",
            message="Database operation failed",
            details=None,
        ),
    )


async def unhandled_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    最终兜底异常处理器。

    只有未被前面处理器识别的异常才会进入这里，例如：

    - 程序逻辑错误；
    - AttributeError；
    - TypeError；
    - 第三方库的未知异常；
    - 响应序列化错误；
    - 开发时遗漏处理的异常。

    该处理器的目标不是“隐藏代码问题”，而是确保：

    1. 客户端始终得到结构化响应；
    2. 客户端看不到服务器堆栈；
    3. 后端日志保留完整异常；
    4. 单次请求失败不会直接破坏整个服务进程。
    """

    log_exception(
        message="Unhandled error",
        request=request,
        exc=exc,
    )

    return JSONResponse(
        status_code=500,
        content=error_body(
            code="INTERNAL_SERVER_ERROR",
            message="Internal server error",
            details=None,
        ),
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    将所有异常处理器注册到 FastAPI 应用中。

    注册关系：

        AppError
            -> app_error_handler

        RequestValidationError
            -> validation_error_handler

        StarletteHTTPException
            -> http_error_handler

        SQLAlchemyError
            -> database_error_handler

        Exception
            -> unhandled_error_handler

    Exception 是最终兜底；
    其他处理器负责更明确、更具体的异常类型。
    """

    app.add_exception_handler(
        AppError,
        app_error_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler,
    )

    app.add_exception_handler(
        StarletteHTTPException,
        http_error_handler,
    )

    app.add_exception_handler(
        SQLAlchemyError,
        database_error_handler,
    )

    app.add_exception_handler(
        Exception,
        unhandled_error_handler,
    )