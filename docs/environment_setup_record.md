# 本地开发环境搭建记录

## 1. 基本信息

- 日期：
- 操作系统：
- 项目目录：
- IDE：
- 接口测试工具：

## 2. 安装前审计

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\check_env.ps1 | Tee-Object -FilePath .\environment_check.txt
```

| 项目 | 检查命令 | 实际版本/状态 | 是否需处理 |
|---|---|---|---|
| Python | `py -0p` |  |  |
| pip | `python -m pip --version` |  |  |
| Git | `git --version` |  |  |
| Docker | `docker version` |  |  |
| Docker Compose | `docker compose version` |  |  |
| WSL | `wsl -l -v` |  |  |
| IDE | `code --version` 等 |  |  |
| Postman/Apifox | `winget list --name ...` |  |  |

## 3. 避免重复下载的决策

- 已有软件：
- 缺少软件：
- 最终新增安装：
- 未安装且原因：
- 是否使用项目 `.venv`：
- Docker Disk image location：

## 4. Python 虚拟环境

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
python -m pip install -r requirements.txt
```

实际输出与说明：

## 5. 公司仓库

- 仓库地址：
- 本地目录：
- 当前分支：
- 依赖管理方式：
- 环境变量文件：
- 数据库启动方式：
- 应用启动命令：

## 6. 运行验证

- `/docs` 地址：
- 是否可访问：
- 接口 1：
- 接口 2：
- Apifox/Postman 截图位置：

## 7. 踩坑记录

### 问题 1

- 现象：
- 原因：
- 排查命令：
- 解决方法：
- 是否复现验证：

## 8. 最终结论

- 本地开发环境是否完整可用：
- 尚未解决的问题：
- 需要导师/同事提供的信息：
