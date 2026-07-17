# 导入类型注解工具，用于将「数据类型 + 校验规则/依赖」打包复用，减少重复代码
from typing import Annotated

# 导入 FastAPI 核心组件：
# APIRouter：路由分组工具，用于把同一模块的接口归为一组，统一管理前缀、标签等
# Depends：依赖注入工具，自动执行依赖函数并注入结果（比如数据库会话）
# Path：路径参数校验器，给 URL 占位符参数加约束
# Query：查询参数校验器，给 URL ? 后的参数加约束
# Response：原生响应对象，用于自定义返回状态码、响应头等
# status：HTTP 状态码常量集合，避免手写魔法数字，更易读
from fastapi import APIRouter, Depends, Path, Query, Response, status
# 导入异步数据库会话类型，用于类型注解
from sqlalchemy.ext.asyncio import AsyncSession

# 导入 CRUD 层（数据库增删改查层）的所有业务操作函数
from app.crud import create_note, delete_note, get_note_by_id, list_notes, patch_note, update_note
# 导入数据库会话的依赖生成函数
from app.database import get_db
# 导入自定义业务异常：笔记不存在异常，会被全局异常处理器捕获返回对应错误
from app.exceptions import NoteNotFoundError
# 导入笔记优先级枚举，保证入参、数据库、出参的枚举值统一
from app.models import NotePriority
# 导入 Pydantic 数据模型：统一错误响应结构、创建/更新/出参 Schema
from app.schemas import ErrorResponse, NoteCreate, NoteOut, NotePatch, NoteUpdate


# 创建笔记模块的路由分组实例
# prefix：统一路由前缀，该分组下所有接口路径都会自动拼接 /notes
# tags：接口文档分组标签，Swagger 文档中会把这些接口归到 notes 分类下
# responses：统一声明该分组所有接口的通用错误响应结构，用于自动生成接口文档
router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)

# 可复用的数据库会话类型注解
# 把「AsyncSession 类型 + Depends(get_db) 依赖注入」打包成一个别名
# 后续接口参数直接写 DbSession 即可，不用每个接口都重复写完整注解
DbSession = Annotated[AsyncSession, Depends(get_db)]

# 可复用的笔记 ID 路径参数注解
# Path(ge=1)：约束路径参数数值必须大于等于 1，避免传入无效的负数或 0
# description：接口文档中展示的参数说明
NoteId = Annotated[int, Path(ge=1, description="Note ID，必须大于等于 1")]


# POST 接口：创建新笔记
# response_model：指定响应数据结构为 NoteOut，自动完成序列化校验和文档生成
# status_code：创建成功默认返回 201 状态码，符合 RESTful 规范
@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note_endpoint(payload: NoteCreate, db: DbSession) -> NoteOut:
    # 1. 调用CRUD层函数写入数据库，返回ORM对象
    # 2. 用model_validate将ORM对象转为响应模型后返回给前端
    return NoteOut.model_validate(await create_note(db, payload))


# GET 接口：分页条件查询笔记列表
# response_model：指定返回值为NoteOut类型的数组
@router.get("", response_model=list[NoteOut])
async def list_notes_endpoint(
    db: DbSession,
    # page：页码，查询参数，最小值为 1，默认第 1 页
    page: Annotated[int, Query(ge=1)] = 1,
    # page_size：每页条数，查询参数，范围限制 1-100，默认每页 20 条
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    # priority：优先级过滤条件，可选参数，不传则不过滤
    priority: NotePriority | None = None,
    # is_archived：归档状态过滤条件，可选参数，不传则不过滤
    is_archived: bool | None = None,
) -> list[NoteOut]:
    # 调用CRUD层执行分页条件查询，得到ORM对象列表
    notes = await list_notes(
        db,
        page=page,
        page_size=page_size,
        priority=priority,
        is_archived=is_archived,
    )
    # 列表推导式：逐个将 ORM 对象转为 NoteOut 响应模型，组成列表返回
    return [NoteOut.model_validate(note) for note in notes]


# GET 接口：根据 ID 查询单条笔记详情
# responses：额外声明该接口 404 错误的响应结构，用于接口文档展示
@router.get("/{note_id}", response_model=NoteOut, responses={404: {"model": ErrorResponse}})
async def get_note_endpoint(note_id: NoteId, db: DbSession) -> NoteOut:
    # 根据主键 ID 查询对应笔记
    note = await get_note_by_id(db, note_id)
    # 查不到对应笔记时，抛出自定义异常
    # 该异常会被全局异常处理器捕获，自动返回 404 格式的错误响应
    if note is None:
        raise NoteNotFoundError()
    # 转为响应模型后返回
    return NoteOut.model_validate(note)


# PUT 接口：全量更新笔记（覆盖所有字段）
# 要求前端传入完整的全部字段，对应 NoteUpdate 全量入参模型
@router.put("/{note_id}", response_model=NoteOut, responses={404: {"model": ErrorResponse}})
async def update_note_endpoint(
    note_id: NoteId,
    payload: NoteUpdate,
    db: DbSession,
) -> NoteOut:
    # 先查询笔记是否存在
    note = await get_note_by_id(db, note_id)
    if note is None:
        raise NoteNotFoundError()
    # 调用 CRUD 层执行全量更新，返回更新后的ORM对象，转响应模型后返回
    return NoteOut.model_validate(await update_note(db, note, payload))


# PATCH 接口：部分更新笔记（仅修改传入的字段）
# 前端只需传入要修改的字段，对应 NotePatch 部分更新入参模型
@router.patch("/{note_id}", response_model=NoteOut, responses={404: {"model": ErrorResponse}})
async def patch_note_endpoint(
    note_id: NoteId,
    payload: NotePatch,
    db: DbSession,
) -> NoteOut:
    # 先查询笔记是否存在
    note = await get_note_by_id(db, note_id)
    if note is None:
        raise NoteNotFoundError()
    # 调用 CRUD 层执行部分更新，返回更新后的 ORM 对象，转响应模型后返回
    return NoteOut.model_validate(await patch_note(db, note, payload))


# DELETE 接口：删除指定笔记
# status_code：删除成功返回 204 状态码（标准语义：请求成功，无响应内容）
# response_model=None：声明没有响应体，避免生成多余的文档结构
@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={404: {"model": ErrorResponse}},
)
async def delete_note_endpoint(note_id: NoteId, db: DbSession) -> Response:
    # 先查询笔记是否存在
    note = await get_note_by_id(db, note_id)
    if note is None:
        raise NoteNotFoundError()
    # 调用 CRUD 层执行删除操作
    await delete_note(db, note)
    # 返回空响应，仅携带 204 状态码
    return Response(status_code=status.HTTP_204_NO_CONTENT)
