# Python 实习 Day 1–Day 2 启动包

> 适用环境：Windows 10/11 + PowerShell  
> 建议把整个目录放在 `D:\Code\python-intern-day12`，虚拟环境、项目代码和练习数据库都会跟随项目放在 D 盘。

## 一、先审计，绝不直接重复安装

打开 PowerShell，进入本目录：

```powershell
cd D:\Code\python-intern-day12
Set-ExecutionPolicy -Scope Process Bypass
.\check_env.ps1 | Tee-Object -FilePath .\environment_check.txt
```

`check_env.ps1` **只检查，不安装、不删除、不修改系统配置**。

重点看：

- Python 是否为 3.11 或更高；
- `py -0p` 中有哪些 Python；
- Git、Docker、Docker Compose、WSL 是否存在；
- VS Code / PyCharm / IntelliJ 是否存在；
- Postman 和 Apifox 是否已有其一；
- 8000、5432、6379 端口是否被占用；
- C/D 盘可用空间；
- Git 用户名、邮箱是否已配置。

## 二、按“缺什么才装什么”处理

### 1. 先确认 WinGet 可用

```powershell
winget --version
winget source list
```

查看软件是否已安装：

```powershell
winget list --name Python
winget list --name "Docker Desktop"
winget list --name Git
winget list --name "Visual Studio Code"
winget list --name PyCharm
winget list --name "IntelliJ IDEA"
winget list --name Postman
winget list --name Apifox
```

只有明确查不到，并且对应命令也不存在时，才安装。

### 2. 缺少软件时的安装命令

```powershell
winget install -e --id Python.Python.3.11
winget install -e --id Git.Git
winget install -e --id Docker.DockerDesktop
winget install -e --id Microsoft.VisualStudioCode
```

接口测试工具只装一个：

```powershell
winget search Postman
winget search Apifox
```

然后根据搜索结果中的精确 ID 安装。已有 Apifox 就不必再装 Postman，反之亦然。

> Python、Git、编辑器本体占用相对有限。真正容易持续挤占 C 盘的是 Docker 镜像、容器和卷。安装 Docker Desktop 后，应在 Docker Desktop 的 Settings → Resources → Advanced 中，将 Disk image location 调到例如 `D:\DockerData`。

## 三、建立项目独立虚拟环境

不要把 FastAPI、Pydantic、SQLAlchemy 装进全局 Python。

先看已有 Python：

```powershell
py -0p
```

如果已有 Python 3.11：

```powershell
py -3.11 -m venv .venv
```

如果只有更高版本，例如 3.12：

```powershell
py -3.12 -m venv .venv
```

激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

若执行策略阻止激活：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

确认当前 Python 确实来自本项目：

```powershell
python --version
python -c "import sys; print(sys.executable)"
python -m pip --version
```

输出路径应包含本项目下的 `.venv`。

安装练习依赖：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

检查是否已经安装，避免重复操作：

```powershell
python -m pip show fastapi
python -m pip show pydantic
python -m pip show sqlalchemy
python -m pip list
```

## 四、Day 1：Pydantic 主线练习

运行：

```powershell
python -m examples.day1_pydantic
```

你应该看到：

1. 合法 Note 模型创建成功；
2. `model_dump()` 输出 Python 字典；
3. `model_dump_json()` 输出 JSON 字符串；
4. `model_validate()` 校验字典；
5. 错误标题、标签过多等输入触发 `ValidationError`；
6. `NoteOut` 通过 `from_attributes=True` 从模拟 ORM 对象转换。

随后阅读并补充：

```text
docs/learning_notes_day1_day2.md
```

## 五、Day 2：FastAPI、依赖、异步与 SQLAlchemy async

### 1. 启动 FastAPI

```powershell
python -m uvicorn app.main:app --reload
```

浏览器打开：

```text
http://127.0.0.1:8000/docs
```

另开一个 PowerShell 测试：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod "http://127.0.0.1:8000/notes?q=python&limit=5"
```

测试 POST：

```powershell
$body = @{
    title = "学习 Pydantic"
    content = "掌握字段约束和校验器"
    priority = "high"
    tags = @("python", "pydantic")
    is_archived = $false
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/notes/preview `
  -ContentType "application/json" `
  -Body $body
```

故意提交错误数据，观察 422：

```powershell
$badBody = @{
    title = "<非法标题>"
    tags = @("1", "2", "3", "4", "5", "6")
} | ConvertTo-Json

try {
    Invoke-RestMethod `
      -Method Post `
      -Uri http://127.0.0.1:8000/notes/preview `
      -ContentType "application/json" `
      -Body $badBody
} catch {
    $_.ErrorDetails.Message
}
```

### 2. 跑 SQLAlchemy 2.0 异步示例

```powershell
python -m examples.day2_sqlalchemy_async
```

运行后会在项目目录生成 `day2_demo.db`。这是 Day 2 学习用 SQLite 文件，不替代公司项目要求的 PostgreSQL/MySQL。

### 3. 运行测试和代码质量检查

```powershell
python -m pytest -q
python -m ruff check .
python -m black --check .
python -m mypy app examples
```

若 Black 只提示格式问题，可执行：

```powershell
python -m black .
```

## 六、验证 Docker，不重复安装数据库

确认 Docker Desktop 已启动：

```powershell
docker version
docker compose version
docker info
```

第一次只做最小验证：

```powershell
docker run --rm hello-world
```

本练习包带有 PostgreSQL + Redis 的 `compose.yaml`：

```powershell
docker compose config
docker compose up -d
docker compose ps
```

查看服务：

```powershell
docker logs intern-postgres --tail 30
docker logs intern-redis --tail 30
docker exec intern-postgres pg_isready -U intern -d intern_db
docker exec intern-redis redis-cli ping
```

停止但保留数据：

```powershell
docker compose stop
```

停止并删除容器：

```powershell
docker compose down
```

## 七、拿到公司仓库后，先识别它使用什么工具

不要一上来同时安装 pip、Poetry、uv、Pipenv。

```powershell
git clone <公司仓库地址> D:\Code\<仓库目录名>
cd D:\Code\<仓库目录名>
Get-ChildItem -Force
Get-ChildItem -Name README*,requirements*.txt,pyproject.toml,poetry.lock,uv.lock,Pipfile,docker-compose*.yml,compose*.yaml,.env.example
```

判断规则：

- 有 `requirements.txt`：通常使用 `python -m pip install -r requirements.txt`
- 有 `uv.lock`：再按 README 使用 uv
- 有 `poetry.lock`：再按 README 使用 Poetry
- 有 `Pipfile`：再按 README 使用 Pipenv
- 有 `compose.yaml` / `docker-compose.yml`：优先看 README 后再 `docker compose up`
- 有 `.env.example`：复制为 `.env`，不要覆盖已有 `.env`

```powershell
Copy-Item .env.example .env
```

查看 Git 状态：

```powershell
git remote -v
git branch --show-current
git status
git log -5 --oneline
```

按仓库 README 启动后验证：

```powershell
Invoke-WebRequest http://127.0.0.1:8000/docs -UseBasicParsing
```

再用 Apifox 或 Postman 调通 2 个已有接口，并保存请求方法、URL、参数、状态码、响应 JSON 和截图。

## 八、Day 1–2 交付物

本启动包已经提供草稿：

- `docs/learning_notes_day1_day2.md`
- `docs/environment_setup_record.md`
- `docs/daily_report_day1.md`
- `docs/daily_report_day2.md`

你需要把脚本输出、真实版本号、公司仓库启动步骤和踩坑补进去。
