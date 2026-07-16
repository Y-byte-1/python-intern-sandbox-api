# 本地开发环境搭建记录

## 1. 基本信息

- **日期**：2026-07-14
- **操作系统**：Windows 家庭中文版，64 位
- **项目目录**：`D:\Code\python_intern_day1_day2_kit`
- **IDE**：Visual Studio Code
- **远程仓库**：`https://github.com/Y-byte-1/python-intern-sandbox-api`
- **接口测试工具**：Postman 


## 2. 环境审计与安装结果

为避免重复安装，先对已有环境进行l了检查，再补充缺少的软件和依赖。

| 项目 | 实际版本或状态 | 处理结果 |
| Python | 3.13.5，位于 `D:\Anaconda\python.exe` | 保留使用 |
| pip | 25.1 | 无需重复安装 |
| Git | 2.46.2 | 已完成用户名、邮箱和默认分支配置 |
| VS Code | 已安装 | 作为项目 IDE |
| WSL | 2.7.10.0，默认版本为 WSL 2 | 新增安装并验证 |
| Docker | 29.6.1 | 新增安装并验证 |
| Docker Compose | v5.3.0 | 随 Docker Desktop 安装 |
| PostgreSQL | `postgres:16-alpine` 容器 | 已启动并通过健康检查 |
| Redis | `redis:7-alpine` 容器 | 已启动并通过健康检查 |

目录规划：

- 开发代码统一放在 `D:\Code`
- 开发工具放在 `D:\Tools`
- Docker Desktop 安装在 `D:\Tools\DockerDesktop`
- Docker 数据存放在 `D:\Tools\DockerData`

## 3. Python 虚拟环境配置

由于本机使用 Anaconda，PowerShell 默认会进入 Conda 的 `base` 环境。为避免项目依赖污染全局环境，项目使用独立的 `.venv`。

```powershell
cd D:\Code\python_intern_day1_day2_kit
conda deactivate
& "D:\Anaconda\python.exe" -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
```

验证解释器：

```powershell
python -c "import sys; print(sys.executable)"
```

实际结果：

```text
D:\Code\python_intern_day1_day2_kit\.venv\Scripts\python.exe
```

安装并检查依赖：

```powershell
python -m pip install -r requirements.txt
python -m pip check
```

检查结果：

```text
No broken requirements found.
```

主要依赖版本：

- FastAPI：0.139.0
- Pydantic：2.13.4
- SQLAlchemy：2.0.51

运行项目已有测试：

```powershell
python -m pytest -q
```

结果：

```text
4 passed, 1 warning
```

4 个测试均通过；warning 为第三方测试依赖的兼容性提醒，当前不影响项目运行。

---

## 4. Docker、PostgreSQL 与 Redis

使用 Docker Desktop 和 WSL 2 作为容器运行环境。现在没有单独安装 Ubuntu 发行版，但 Docker Desktop 自带的 `docker-desktop` WSL 2 环境已经能够正常运行 Linux 容器。

Docker 基础验证：

```powershell
docker run --rm hello-world
```

成功输出：

```text
Hello from Docker!
```

使用 Compose 启动数据库服务：

```powershell
docker compose config
docker compose up -d
docker compose ps
```

运行状态：

- `intern-postgres`：`healthy`
- `intern-redis`：`healthy`

PostgreSQL 验证：

```powershell
docker exec intern-postgres pg_isready -U intern -d intern_db
```

结果：

```text
/var/run/postgresql:5432 - accepting connections
```

Redis 验证：

```powershell
docker exec intern-redis redis-cli ping
```

结果：

```text
PONG
```

端口映射：

- PostgreSQL：`127.0.0.1:5432`
- Redis：`127.0.0.1:6379`

---

## 5. Git 与 GitHub

Git 全局配置：

```text
user.name = Jia Tang
user.email = 243597031+Y-byte-1@users.noreply.github.com
init.defaultBranch = main
```

项目仓库初始化和推送过程：

```powershell
git init
git add .
git commit -m "feat: initialize FastAPI sandbox project"
git remote add origin https://github.com/Y-byte-1/python-intern-sandbox-api.git
git branch -M main
git push -u origin main
```

首次提交：

```text
6489850 feat: initialize FastAPI sandbox project
```

已确认 GitHub 仓库中能够看到项目文件，说明本地仓库、远程仓库关联和代码推送均已完成。

---

## 6. 重点踩坑记录

### 6.1 PowerShell 中文脚本乱码

- **现象**：环境检查脚本出现中文乱码和解析错误。
- **原因**：Windows PowerShell 5.1 对部分无 BOM 的 UTF-8 中文脚本兼容性较差。
- **解决方法**：将检查脚本改为英文 ASCII 版本后重新运行。

### 6.2 Conda base 与项目 `.venv` 混淆

- **现象**：PowerShell 默认显示 `(base)`，存在依赖安装到全局环境的风险。
- **解决方法**：

```powershell
conda deactivate
.\.venv\Scripts\Activate.ps1
```

并使用下列命令确认解释器路径：

```powershell
python -c "import sys; print(sys.executable)"
```

### 6.3 PowerShell 限制激活脚本

- **现象**：`.venv\Scripts\Activate.ps1` 可能被执行策略阻止。
- **解决方法**：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```
该设置仅对当前 PowerShell 窗口生效，关闭窗口后自动失效。
### 6.4 Docker Hub 镜像拉取失败

- **现象**：拉取镜像时出现 `TLS handshake timeout` 或 `EOF`。
- **原因**：当前网络无法稳定直连 Docker Hub，需要通过本地代理访问。
- **解决方法**：
  - 使用 Windows 系统代理 `127.0.0.1:9674`
  - 在 Docker Desktop 中启用系统代理
  - 出现一次性 EOF 后重新执行拉取命令
最终 `hello-world`、PostgreSQL 和 Redis 镜像均成功下载并运行。
### 6.5 GitHub 仓库最初为空

- **现象**：本地已经执行 `git commit`，但 GitHub 页面仍显示空仓库。
- **原因**：Commit后只保存在本地，尚未执行Push。
- **解决方法**：
```powershell
git push -u origin main
```
执行后刷新 GitHub 页面，项目文件正常显示。

### 6.6 LF/CRLF 提示

- **现象**：出现 `LF will be replaced by CRLF`。
- **说明**：这是 Windows 与 Linux 换行符差异的提示，不是提交失败，不影响当前 Python 项目运行。

---

## 7. 当前完成情况

### 已完成

- Python 和 pip 环境检查
- 项目 `.venv` 创建与依赖安装
- Pydantic 示例运行
- pytest 测试通过
- WSL 2 安装
- Docker Desktop 安装与验证
- PostgreSQL、Redis 容器启动与健康检查
- Git 初始化、Commit、远程仓库关联与 Push
- GitHub 仓库文件确认

### 待完成

- 从 GitHub 重新 Clone 到新目录并独立运行
- 使用 IDE 打开 Clone 后的项目
- 启动 FastAPI 并验证 `/docs`
- 使用 Apifox/Postman 调通两个已有接口

---

## 8. 最终结论

当前本地 Python、Git、WSL、Docker、PostgreSQL 和 Redis 基础开发环境均已配置完成并通过验证，项目依赖无冲突，自动测试通过，代码已成功推送到 GitHub。

后续重点是完成“Clone 后独立运行、`/docs` 访问以及两个接口调试”，形成完整的项目拉取、启动和接口验证流程。