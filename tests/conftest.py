"""pytest 公共配置：项目根入 sys.path + offscreen Qt + QApplication fixture"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def app():
    """会话级 QApplication（offscreen，勿跑事件循环）。"""
    a = QApplication.instance() or QApplication([])
    return a
