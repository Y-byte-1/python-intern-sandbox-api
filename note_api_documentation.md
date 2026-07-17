要求 Note 模块包含 6 个 CRUD 接口，并满足 Schema 分离、PATCH 只更新传入字段、异步接口、统一 404/422/500 错误格式等要求。

````markdown
# Note 便签模块接口文档

## 1. 文档说明

- 模块名称：Note 便签管理
- 服务名称：Python Intern Sandbox API
- 基础地址：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- OpenAPI 文档：`http://127.0.0.1:8000/openapi.json`
- 请求数据格式：`application/json`
- 响应数据格式：`application/json`
- 数据库：PostgreSQL
- 数据库访问方式：SQLAlchemy2.0 Async ORM
- 接口实现方式：FastAPI `async def`
---

# 2. Note 数据结构

## 2.1 Note 字段说明

| 字段 | 类型 | 是否必填 | 是否可为 null | 默认值 | 说明 |
|---|---|---:|---:|---|---|
| `id` | integer | 响应必有 | 否 | 数据库生成 | Note 主键 |
| `title` | string | 是 | 否 | 无 | 标题，长度 1～100 |
| `content` | string | 否 | 是 | `null` | 内容，最长 10000 字 |
| `priority` | string | 否 | 否 | `medium` | 优先级，只能为 `low`、`medium`、`high` |
| `tags` | array[string] | 否 | 否 | `[]` | 最多 5 个标签，每个标签长度 1～20 |
| `is_archived` | boolean | 否 | 否 | `false` | 是否归档 |
| `created_at` | datetime | 响应必有 | 否 | 数据库生成 | 创建时间 |
| `updated_at` | datetime | 响应必有 | 否 | 数据库生成 | 最后更新时间 |

---

# 3. 请求与响应Schema

## 3.1 NoteCreate

用于：

```text
POST /notes
````

```json
{
  "title": "学习 FastAPI",
  "content": "完成 Note CRUD 接口",
  "priority": "high",
  "tags": [
    "python",
    "fastapi"
  ],
  "is_archived": false
}
```

字段要求：

| 字段            | 类型            | 必填 | 默认值      |
| ------------- | ------------- | -: | -------- |
| `title`       | string        |  是 | 无        |
| `content`     | string 或 null |  否 | `null`   |
| `priority`    | string        |  否 | `medium` |
| `tags`        | array[string] |  否 | `[]`     |
| `is_archived` | boolean       |  否 | `false`  |

---

## 3.2 NoteUpdate

用于：

```text
PUT /notes/{note_id}
```

PUT 表示全量更新，因此所有可修改字段都必须在请求体中出现。

```json
{
  "title": "更新后的标题",
  "content": "更新后的内容",
  "priority": "medium",
  "tags": [
    "python",
    "database"
  ],
  "is_archived": false
}
```

字段要求：

| 字段            | 类型            | 必填 | 是否可为 null |
| ------------- | ------------- | -: | --------: |
| `title`       | string        |  是 |         否 |
| `content`     | string 或 null |  是 |         是 |
| `priority`    | string        |  是 |         否 |
| `tags`        | array[string] |  是 |         否 |
| `is_archived` | boolean       |  是 |         否 |

说明：

* 即使 `content` 没有内容，也应明确传入 `null`。
* 缺少任意必填字段时返回 HTTP 422。
* PUT 会使用请求体整体替换原有可修改字段。

---

## 3.3 NotePatch

用于：

```text
PATCH/notes/{note_id}
```

PATCH 表示部分更新，只需要传入需要修改的字段。

例如只修改优先级：

```json
{
  "priority": "high"
}
```

例如修改内容并归档：

```json
{
  "content": "该任务已经完成",
  "is_archived": true
}
```

字段要求：

| 字段            | 类型            | 必填 | 是否可为 null |
| ------------- | ------------- | -: | --------: |
| `title`       | string        |  否 |         否 |
| `content`     | string 或 null |  否 |         是 |
| `priority`    | string        |  否 |         否 |
| `tags`        | array[string] |  否 |         否 |
| `is_archived` | boolean       |  否 |         否 |

说明：

* 请求体至少包含一个字段。
* 未传入的字段保持原值。
* `content` 可以明确更新为 `null`。
* `title`、`priority`、`tags`、`is_archived` 不允许传入 `null`。
* 后端使用：

```python
payload.model_dump(exclude_unset=True)
```
获取用户实际传入的字段。

---

## 3.4 NoteOut

所有查询、创建和更新成功后使用该结构返回。

```json
{
  "id": 1,
  "title": "学习 FastAPI",
  "content": "完成 Note CRUD 接口",
  "priority": "high",
  "tags": [
    "python",
    "fastapi"
  ],
  "is_archived": false,
  "created_at": "2026-07-15T08:30:00+00:00",
  "updated_at": "2026-07-15T08:30:00+00:00"
}
```

字段要求：

| 字段            | 类型            | 说明    |
| ------------- | ------------- | ----- |
| `id`          | integer       | 数据库主键 |
| `title`       | string        | 标题    |
| `content`     | string 或 null | 内容    |
| `priority`    | string        | 优先级   |
| `tags`        | array[string] | 标签列表  |
| `is_archived` | boolean       | 是否归档  |
| `created_at`  | datetime      | 创建时间  |
| `updated_at`  | datetime      | 更新时间  |

Pydantic 配置：

```python
model_config = ConfigDict(from_attributes=True)
```

该配置允许直接将SQLAlchemy ORM对象转换为 `NoteOut`。

---

# 4. 统一错误响应 Schema

HTTP 404、422、500 使用统一结构：

```json
{
  "code": "ERROR_CODE",
  "message": "错误说明",
  "details": null
}
```

字段说明：

| 字段        | 类型                  | 说明         |
| --------- | ------------------- | ---------- |
| `code`    | string              | 程序可识别的错误编码 |
| `message` | string              | 面向调用方的错误说明 |
| `details` | object、array 或 null | 详细错误信息     |

---

## 4.1 404 示例

```json
{
  "code": "NOTE_NOT_FOUND",
  "message": "Note not found",
  "details": null
}
```

---

## 4.2 422 示例

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {
      "field": "body.title",
      "message": "String should have at least 1 character",
      "type": "string_too_short"
    }
  ]
}
```

---

## 4.3 500 示例

```json
{
  "code": "INTERNAL_SERVER_ERROR",
  "message": "Internal server error",
  "details": null
}
```

注意：

* 500 响应不能直接返回数据库密码、SQL 语句、文件路径或完整异常堆栈。
* 详细异常只记录在后端日志中。

---

# 5. 接口清单

| 方法     | URL                | 说明           |
| ------ | ------------------ | ------------ |
| POST   | `/notes`           | 创建 Note      |
| GET    | `/notes`           | 分页查询 Note 列表 |
| GET    | `/notes/{note_id}` | 查询 Note 详情   |
| PUT    | `/notes/{note_id}` | 全量更新 Note    |
| PATCH  | `/notes/{note_id}` | 部分更新 Note    |
| DELETE | `/notes/{note_id}` | 删除 Note      |

---

# 6. 创建 Note

## URL

```text
/notes
```

## 方法

```text
POST
```

## 请求 Schema

```text
NoteCreate
```

请求示例：

```json
{
  "title": "学习 PostgreSQL",
  "content": "使用 FastAPI 和 SQLAlchemy 创建便签",
  "priority": "high",
  "tags": [
    "python",
    "database"
  ],
  "is_archived": false
}
```

## 成功响应

状态码：

```text
201 Created
```

响应 Schema：

```text
NoteOut
```

响应示例：

```json
{
  "id": 1,
  "title": "学习 PostgreSQL",
  "content": "使用 FastAPI 和 SQLAlchemy 创建便签",
  "priority": "high",
  "tags": [
    "python",
    "database"
  ],
  "is_archived": false,
  "created_at": "2026-07-15T08:30:00+00:00",
  "updated_at": "2026-07-15T08:30:00+00:00"
}
```

## 错误码

| 状态码 | code                    | 场景                |
| --: | ----------------------- | ----------------- |
| 422 | `VALIDATION_ERROR`      | 请求字段格式、类型或长度不符合要求 |
| 500 | `INTERNAL_SERVER_ERROR` | 数据库提交失败或服务器内部异常   |

## 校验规则说明

* `title` 必填。
* `title` 去除首尾空格后长度必须为 1～100。
* `title` 不能包含 `<` 或 `>`。
* `content` 最长 10000 字，可以为 `null`。
* `priority` 只能为 `low`、`medium`、`high`。
* 未传 `priority` 时默认为 `medium`。
* `tags` 最多5个。
* 每个标签去除首尾空格后长度为 1～20。
* 标签不能重复，重复判断忽略大小写。
* 未传`tags`时默认为空数组。
* 未传`is_archived`时默认为 `false`。
* 不允许出现Schema中未声明的额外字段。

---

# 7. 查询 Note 列表

## URL

```text
/notes
```

## 方法

```text
GET
```

## 请求 Schema

无JSON请求体，通过Query参数传递。

| 参数            | 类型      | 必填 | 默认值 | 校验规则                  |
| ------------- | ------- | -: | --: | --------------------- |
| `page`        | integer |  否 |   1 | 大于或等于 1               |
| `page_size`   | integer |  否 |  20 | 1～100                 |
| `priority`    | string  |  否 |   无 | `low`、`medium`、`high` |
| `is_archived` | boolean |  否 |   无 | `true` 或 `false`      |

请求示例：

```text
GET/notes?page=1&page_size=20
```

按优先级和归档状态筛选：

```text
GET/notes?page=1&page_size=20&priority=high&is_archived=false
```

## 成功响应

状态码：

```text
200 OK
```

响应 Schema：

```text
array[NoteOut]
```

响应示例：

```json
[
  {
    "id": 2,
    "title": "完成接口测试",
    "content": null,
    "priority": "high",
    "tags": [
      "postman"
    ],
    "is_archived": false,
    "created_at": "2026-07-15T09:00:00+00:00",
    "updated_at": "2026-07-15T09:00:00+00:00"
  },
  {
    "id": 1,
    "title": "学习 PostgreSQL",
    "content": "使用 FastAPI 和 SQLAlchemy 创建便签",
    "priority": "high",
    "tags": [
      "python",
      "database"
    ],
    "is_archived": false,
    "created_at": "2026-07-15T08:30:00+00:00",
    "updated_at": "2026-07-15T08:30:00+00:00"
  }
]
```

查询不到数据时：

```json
[]
```

## 错误码

| 状态码 | code                    | 场景         |
| --: | ----------------------- | ---------- |
| 422 | `VALIDATION_ERROR`      | 分页或筛选参数不合法 |
| 500 | `INTERNAL_SERVER_ERROR` | 数据库查询失败    |

## 校验规则说明

* `page` 必须大于或等于 1。
* `page_size` 必须在 1～100 之间。
* `priority` 只能为指定枚举值。
* `is_archived` 只能转换为布尔值。
* 不传筛选参数时查询全部 Note。
* 返回结果按 `id` 倒序排列。
* 没有结果时返回空数组，不返回 404。

---

# 8. 查询 Note 详情

## URL

```text
/notes/{note_id}
```

## 方法

```text
GET
```

## 请求 Schema

无 JSON 请求体。

路径参数：

| 参数        | 类型      | 必填 | 校验规则    |
| --------- | ------- | -: | ------- |
| `note_id` | integer |  是 | 大于或等于 1 |

请求示例：

```text
GET /notes/1
```

## 成功响应

状态码：

```text
200 OK
```

响应 Schema：

```text
NoteOut
```

响应示例：

```json
{
  "id": 1,
  "title": "学习 PostgreSQL",
  "content": "使用 FastAPI 和 SQLAlchemy 创建便签",
  "priority": "high",
  "tags": [
    "python",
    "database"
  ],
  "is_archived": false,
  "created_at": "2026-07-15T08:30:00+00:00",
  "updated_at": "2026-07-15T08:30:00+00:00"
}
```

## 错误码

| 状态码 | code                    | 场景                |
| --: | ----------------------- | ----------------- |
| 404 | `NOTE_NOT_FOUND`        | 指定 ID 的 Note 不存在  |
| 422 | `VALIDATION_ERROR`      | `note_id` 不是合法正整数 |
| 500 | `INTERNAL_SERVER_ERROR` | 数据库查询失败           |

## 校验规则说明

* `note_id` 必须是正整数。
* Note 不存在时返回 404。
* 不能使用空对象或 `null` 表示不存在。

---

# 9. 全量更新 Note

## URL

```text
/notes/{note_id}
```

## 方法

```text
PUT
```

## 请求 Schema

```text
NoteUpdate
```

请求示例：

```json
{
  "title": "完整更新后的标题",
  "content": "完整更新后的内容",
  "priority": "medium",
  "tags": [
    "python",
    "update"
  ],
  "is_archived": false
}
```

## 成功响应

状态码：

```text
200 OK
```

响应 Schema：

```text
NoteOut
```

## 错误码

| 状态码 | code                    | 场景               |
| --: | ----------------------- | ---------------- |
| 404 | `NOTE_NOT_FOUND`        | 指定 ID 的 Note 不存在 |
| 422 | `VALIDATION_ERROR`      | 路径参数或请求体不合法      |
| 500 | `INTERNAL_SERVER_ERROR` | 数据库更新失败          |

## 校验规则说明

* `note_id` 必须为正整数。
* PUT 必须传入全部 5 个可修改字段。
* `content` 可以明确传入 `null`。
* 其他字段不得为 `null`。
* 字段约束与 `NoteCreate` 相同。
* 更新成功后必须刷新并返回数据库中的最新对象。
* `updated_at` 应自动更新。

---

# 10. 部分更新 Note

## URL

```text
/notes/{note_id}
```

## 方法

```text
PATCH
```

## 请求 Schema

```text
NotePatch
```

请求示例：

```json
{
  "priority": "low",
  "is_archived": true
}
```

## 成功响应

状态码：

```text
200 OK
```

响应 Schema：

```text
NoteOut
```

## 错误码

| 状态码 | code                    | 场景                |
| --: | ----------------------- | ----------------- |
| 404 | `NOTE_NOT_FOUND`        | 指定 ID 的 Note 不存在  |
| 422 | `VALIDATION_ERROR`      | 请求体为空、字段非法或路径参数非法 |
| 500 | `INTERNAL_SERVER_ERROR` | 数据库更新失败           |

## 校验规则说明

* 请求体至少包含一个允许更新的字段。
* 未传入的字段保持数据库原值。
* 使用：

```python
payload.model_dump(exclude_unset=True)
```

提取实际传入字段。

* `content` 可以明确更新为 `null`。
* `title` 不允许更新为 `null`。
* `priority` 不允许更新为 `null`。
* `tags` 不允许更新为 `null`。
* `is_archived` 不允许更新为 `null`。
* 字段非空时仍需满足长度、枚举和标签校验规则。
* 更新后 `updated_at` 自动变化。

---

# 11. 删除 Note

## URL

```text
/notes/{note_id}
```

## 方法

```text
DELETE
```

## 请求 Schema

无 JSON 请求体。

请求示例：

```text
DELETE /notes/1
```

## 成功响应

状态码：

```text
204 No Content
```

响应体：

```text
无响应体
```

## 错误码

| 状态码 | code                    | 场景                |
| --: | ----------------------- | ----------------- |
| 404 | `NOTE_NOT_FOUND`        | 指定 ID 的 Note 不存在  |
| 422 | `VALIDATION_ERROR`      | `note_id` 不是合法正整数 |
| 500 | `INTERNAL_SERVER_ERROR` | 数据库删除失败           |

## 校验规则说明

* `note_id` 必须是正整数。
* 删除不存在的数据时返回 404。
* 删除成功后返回 204。
* 204 响应不能包含 JSON 响应体。
* 当前设计为物理删除，即从数据库中真正删除该记录。

---

# 12. Postman 验证清单

## 创建接口

* [ ] 合法创建返回 201
* [ ] 不传 `title` 返回 422
* [ ] `title` 为空返回 422
* [ ] `title` 超过 100 字返回 422
* [ ] `title` 包含 `<` 或 `>` 返回 422
* [ ] `priority` 为非法值返回 422
* [ ] `tags` 超过 5 个返回 422
* [ ] 单个标签超过 20 字返回 422
* [ ] 重复标签返回 422
* [ ] 出现未知字段返回 422

## 列表接口

* [ ] 默认分页查询返回 200
* [ ] `page=0` 返回 422
* [ ] `page_size=101` 返回 422
* [ ] 按 `priority` 筛选成功
* [ ] 按 `is_archived` 筛选成功
* [ ] 无数据返回空数组

## 详情接口

* [ ] 查询已存在 ID 返回 200
* [ ] 查询不存在 ID 返回 404
* [ ] 非整数 ID 返回 422
* [ ] ID 小于 1 返回 422

## PUT 接口

* [ ] 全部字段合法时返回 200
* [ ] 缺少任一字段返回 422
* [ ] 不存在 ID 返回 404
* [ ] 更新后 `updated_at` 改变

## PATCH 接口

* [ ] 只更新一个字段成功
* [ ] 未传入字段保持原值
* [ ] 空对象 `{}` 返回 422
* [ ] `content: null` 可以成功
* [ ] `title: null` 返回 422
* [ ] 不存在 ID 返回 404

## DELETE 接口

* [ ] 删除已存在 ID 返回 204
* [ ] 删除后再次查询返回 404
* [ ] 删除不存在 ID 返回 404
