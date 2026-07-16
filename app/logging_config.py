"""
项目日志配置。

日志同时输出到：
1. PowerShell / IDE 终端；
2. 项目根目录 logs/app.log；
3. 严重错误额外保存到 logs/error.log。
"""

import logging
from logging.config import dictConfig
from pathlib import Path


# 当前文件：
# D:\Code\python_intern_day1_day2_kit\app\logging_config.py
#
# parent       -> app
# parent.parent -> 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 日志文件夹：
# D:\Code\python_intern_day1_day2_kit\logs
LOG_DIR = PROJECT_ROOT / "logs"

# 文件夹不存在时自动创建。
LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"


def configure_logging() -> None:
    """配置项目全局日志。"""

    logging_config = {
        # dictConfig 配置格式版本，目前固定使用 1。
        "version": 1,

        # False 表示不要禁用第三方库已经创建的 Logger。
        "disable_existing_loggers": False,

        # 定义日志输出格式。
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s | "
                    "%(levelname)s | "
                    "%(name)s | "
                    "%(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s | "
                    "%(levelname)s | "
                    "%(name)s | "
                    "%(filename)s:%(lineno)d | "
                    "%(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },

        # Handler 决定日志输出到哪里。
        "handlers": {
            # 输出到 PowerShell 或 VS Code 终端。
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },

            # 保存所有 INFO 及以上日志。
            "app_file": {
                "class": (
                    "logging.handlers."
                    "RotatingFileHandler"
                ),
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(APP_LOG_FILE),
                "encoding": "utf-8",

                # 单个日志文件最大约 10 MB。
                "maxBytes": 10 * 1024 * 1024,

                # 最多保留 5 个历史文件。
                "backupCount": 5,

                # 第一次真正写日志时再打开文件。
                "delay": True,
            },

            # 单独保存 ERROR 和 CRITICAL 日志。
            "error_file": {
                "class": (
                    "logging.handlers."
                    "RotatingFileHandler"
                ),
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(ERROR_LOG_FILE),
                "encoding": "utf-8",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "delay": True,
            },
        },

        # 根 Logger。
        #
        # 其他模块通过 logging.getLogger(__name__)
        # 获得的 Logger，默认会把日志向上传播到根 Logger。
        "root": {
            "level": "INFO",
            "handlers": [
                "console",
                "app_file",
                "error_file",
            ],
        },

        # 单独配置项目 Logger。
        "loggers": {
            "app": {
                "level": "INFO",

                # 不单独绑定 Handler，而是传播给 root。
                "handlers": [],
                "propagate": True,
            },

            # 让 Uvicorn 的错误日志也进入项目日志。
            "uvicorn.error": {
                "level": "INFO",
                "handlers": [],
                "propagate": True,
            },

            # 记录 HTTP 访问日志。
            "uvicorn.access": {
                "level": "INFO",
                "handlers": [],
                "propagate": True,
            },
        },
    }

    dictConfig(logging_config)