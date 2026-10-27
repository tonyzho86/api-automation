"""环境配置 —— 所有"会变的东西"集中在这里。

原则:**用例里禁止硬编码** 地址、账号、路径。换测试环境时只改 .env,不动一行代码。
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录:framework/config/settings.py -> 上溯三级
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(PROJECT_ROOT / ".env")

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:18800")
TIMEOUT = float(os.getenv("API_TIMEOUT", "10"))

# 测试账号
USER = os.getenv("TEST_USER", "alice")
PASSWORD = os.getenv("TEST_PASSWORD", "123456")
ADMIN = os.getenv("TEST_ADMIN", "admin")
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "admin123")
