"""
Note 模块的数据校验与响应模型。

该文件使用 Pydantic v2 定义接口的数据结构，主要负责：

1. 校验客户端提交的请求数据；
2. 限制字段长度、类型和取值范围；
3. 为部分字段设置默认值；
4. 区分 POST、PUT、PATCH 三种请求的数据结构；
5. 将 SQLAlchemy ORM 对象转换为接口响应；
6. 定义统一的错误响应格式。

注意：
schemas.py 面向的是“接口数据”，并不直接定义数据库表。

数据库表结构定义在：
    app/models.py
"""


# 导入日期时间类型，用于存储和传递时间字段
from datetime import datetime
# 导入类型注解工具：
# Annotated：给类型附加额外约束/信息，实现类型规则复用
# Any：表示任意数据类型
# Self：表示方法返回值是当前类的实例自身
from typing import Annotated, Any, Self

# 导入 Pydantic 核心组件：
# BaseModel：所有数据模型的基类
# ConfigDict：用于配置模型的全局行为
# Field：给字段添加长度、范围等约束规则
# field_validator：单字段自定义校验器
# model_validator：全模型/跨字段自定义校验器
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# 导入 ORM 层定义的优先级枚举，保证入参、数据库、出参的枚举值统一
from app.models import NotePriority


# ---------- 可复用字段类型别名 ----------
# 使用 Annotated 将「字段类型 + Field 约束」打包成一个可复用的类型
# 好处：多个模型用到同类型字段时，不用重复写约束，修改规则只改一处
# 标题字段：字符串类型，长度限制 1~100 个字符
Title = Annotated[str, Field(min_length=1, max_length=100)]
# 内容字段：可为空的字符串，最大长度 10000 字符
Content = Annotated[str | None, Field(max_length=10000)]
# 单个标签字段：字符串类型，长度限制 1~20 个字符
Tag = Annotated[str, Field(min_length=1, max_length=20)]


# ---------- 自定义字段清洗/校验工具函数 ----------
# 标题清洗逻辑：去除首尾空格 + 校验非法字符
# 抽成独立函数，方便多个模型的校验器复用同一份规则
def clean_title(value: Any) -> Any:
    # 仅当传入值是字符串时，才执行清洗和校验
    if isinstance(value, str):
        # 去除字符串首尾的空格、换行等空白字符
        value = value.strip()
        # 简单安全校验：禁止包含 < 和 > 字符，降低 XSS 注入风险
        if "<" in value or ">" in value:
            raise ValueError("title 不能包含特殊字符 < 或 >")
    # 返回清洗后的值
    return value


# 标签列表清洗逻辑：去空格 + 去重校验
def clean_tags(value: Any) -> Any:
    # 如果值为空 / 不是列表，直接返回，交给后续的类型校验处理
    if value is None or not isinstance(value, list):
        return value
    # 如果列表元素不全是字符串，直接返回，交给后续的类型校验处理
    if not all(isinstance(item, str) for item in value):
        return value
    # 第一步：对每个标签去除首尾空格
    cleaned = [item.strip() for item in value]
    # 第二步：全部转为小写，用于不区分大小写的重复判断
    normalized = [item.casefold() for item in cleaned]
    # 利用集合去重特性判断：去重后长度和原长度不一致，说明存在重复标签
    if len(normalized) != len(set(normalized)):
        raise ValueError("tags 不能重复")
    # 返回清洗后的标签列表
    return cleaned


# ---------- 笔记模型公共基类 ----------
# 所有笔记相关的入参模型都继承这个基类，复用公共字段和公共校验
class NoteBase(BaseModel):
    # 模型全局配置：extra="forbid" 禁止传入模型未定义的多余字段
    # 作用：严格控制入参，防止前端传入脏数据、无关字段
    model_config = ConfigDict(extra="forbid")

    # 标题：复用上面定义的 Title 类型，自带长度约束
    title: Title
    # 内容：可空字段，默认值为 None
    content: Content = None
    # 优先级：枚举类型，默认值为中等优先级
    priority: NotePriority = NotePriority.medium
    # 标签列表：每个元素是 Tag 类型，默认是空列表，最多允许 5 个标签
    # default_factory=list：每次实例化都生成新的空列表，避免所有实例共享同一个列表（Python 可变默认值坑）
    tags: list[Tag] = Field(default_factory=list, max_length=5)
    # 是否已归档：布尔类型，默认未归档
    is_archived: bool = False

    # 单字段校验器：针对 title 字段
    # mode="before"：在 Pydantic 做类型校验之前先执行这个函数（先清洗数据，再校验类型）
    # @classmethod：类方法，第一个参数是类本身 cls
    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: Any) -> Any:
        # 调用上面的清洗函数处理标题
        return clean_title(value)

    # 单字段校验器：针对 tags 字段，同样在类型校验前执行
    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value: Any) -> Any:
        # 调用上面的清洗函数处理标签列表
        return clean_tags(value)


"""
第五部分
NoteCreate
NoteOut
定义创建和响应 Schema
"""


# 创建笔记的入参模型
# 完全继承 NoteBase 的所有字段和校验规则，无额外字段，用 pass 占位
class NoteCreate(NoteBase):
    pass


# 全量更新笔记的入参模型（PUT 请求用）
# 全量更新要求所有字段必须传，因此重写字段、去掉默认值，使其变为必填
class NoteUpdate(NoteBase):
    content: Content
    priority: NotePriority
    tags: list[Tag] = Field(max_length=5)
    is_archived: bool


# 部分更新笔记的入参模型（PATCH 请求用）
# 部分更新允许只传要修改的字段，所有字段都可选
class NotePatch(BaseModel):
    # 同样禁止传入多余字段
    model_config = ConfigDict(extra="forbid")

    # 所有字段都声明为「可选 + 默认 None」：不传就不修改，传了才更新
    title: Title | None = None
    content: Content = None
    priority: NotePriority | None = None
    tags: list[Tag] | None = Field(default=None, max_length=5)
    is_archived: bool | None = None

    # 标题字段校验：和基类保持一致的清洗逻辑
    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: Any) -> Any:
        return clean_title(value)

    # 标签字段校验：和基类保持一致的清洗逻辑
    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value: Any) -> Any:
        return clean_tags(value)

    # 全模型校验器：mode="after" 表示所有单字段校验完成后再执行
    # 用于做跨字段、整体业务规则校验
    @model_validator(mode="after")
    def validate_patch_body(self) -> Self:
        # model_fields_set：记录用户实际传入了哪些字段
        # 如果一个字段都没传，直接报错：PATCH 请求至少要修改一项
        if not self.model_fields_set:
            raise ValueError("PATCH 请求至少需要包含一个字段")
        # 遍历指定字段：如果用户明确传了该字段，但值是 null，报错
        # 区分「没传字段（不修改）」和「传了 null（要设为空）」两种场景
        for field_name in {"title", "priority", "tags", "is_archived"}:
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} 不能为 null")
        # 校验通过，返回模型自身
        return self


# 笔记响应模型（返回给前端的数据结构）
class NoteOut(NoteBase):
    # 配置：
    # 1. from_attributes=True：支持直接从 ORM 对象转换为该模型
    # 2. extra="forbid"：输出时也严格控制字段，避免泄露多余数据
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    # 笔记主键 ID
    id: int
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime


# ---------- 统一错误响应模型 ----------
# 单条错误详情结构，对应 422 错误里的每一项明细
class ErrorDetail(BaseModel):
    # 出错字段的路径，例如 body.title
    field: str
    # 错误描述文案，可直接展示给用户
    message: str
    # 标准化错误类型编码，例如 string_too_short
    type: str


# 整体错误响应结构，所有接口错误统一返回该格式
class ErrorResponse(BaseModel):
    # 业务错误码，例如 VALIDATION_ERROR
    code: str
    # 错误总描述
    message: str
    # 详细错误信息，支持列表、字典或者空三种形式
    details: list[ErrorDetail] | dict[str, Any] | None = None
