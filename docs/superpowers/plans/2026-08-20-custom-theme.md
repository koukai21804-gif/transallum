# 自定义主题功能实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 让用户自定义全部 24 个主题颜色（hex 输入 + 色轮），并为窗口/导航栏分别设置背景图片（jpg/png）与透明度；自定义颜色作为覆盖层叠加在深浅主题上并持久化。

**架构：** 新增 `utils/theme_settings.py`（JSON 持久化 + 颜色合并）、`gui/background.py`（AppBackground/SidebarBackground 两个 paintEvent 背景层）、`gui/theme_settings_dialog.py`（设置对话框）。`gui/main_window.py` 收敛 `apply_theme()` 单一入口；QSS 中 contentStack/sidebar 改透明，由背景层绘制底色与图片。

**技术栈：** Python 3.12 / PyQt6 / pytest（新增，装进 D 盘 venv）

**测试运行方式：** `./venv/Scripts/python.exe -m pytest tests/ -v`（沙箱限制：勿直接 `python file.py`；QT_QPA_PLATFORM=offscreen 由 conftest 设置）

---

## 文件结构

- 创建 `utils/theme_settings.py` — 设置存取 / merge / COLOR_SLOTS
- 创建 `gui/background.py` — 背景绘制层
- 创建 `gui/theme_settings_dialog.py` — 设置对话框
- 创建 `tests/conftest.py` — sys.path + offscreen Qt + `app` fixture
- 创建 `tests/test_theme_settings.py` / `tests/test_themes.py` / `tests/test_background.py` / `tests/test_theme_dialog.py` / `tests/test_main_window.py`
- 创建 `requirements-dev.txt` — pytest
- 修改 `utils/themes.py` — contentStack/sidebar 透明
- 修改 `utils/i18n.py` — 对话框文案
- 修改 `gui/main_window.py` — apply_theme / 背景层 / 设置按钮
- 修改 `main.py` — 无需改动（首帧兜底样式保留，MainWindow 启动即覆盖）

---

### 任务 0：测试基础设施

**文件：**
- 创建：`tests/conftest.py`
- 创建：`requirements-dev.txt`

- [ ] **步骤 1：安装 pytest 到 D 盘 venv**

```bash
./venv/Scripts/python.exe -m pip install pytest
```

- [ ] **步骤 2：创建 requirements-dev.txt**

```
-r requirements.txt
pytest
```

- [ ] **步骤 3：创建 tests/conftest.py**

```python
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
```

- [ ] **步骤 4：验证基础设施**

```bash
./venv/Scripts/python.exe -m pytest tests/ -v
```

预期：`no tests ran`（尚无测试），退出码 0。若 `utils`/`gui` 导入报错，先修 conftest。

- [ ] **步骤 5：Commit**

```bash
git add tests/conftest.py requirements-dev.txt
git commit -m "chore: 引入 pytest 测试基础设施（offscreen Qt + sys.path）"
```

---

### 任务 1：utils/theme_settings.py — 持久化与合并

**文件：**
- 创建：`utils/theme_settings.py`
- 测试：`tests/test_theme_settings.py`

- [ ] **步骤 1：编写失败的测试**

```python
import copy
import json

import pytest

from utils.theme_settings import (
    COLOR_SLOTS,
    DEFAULT_SETTINGS,
    load_settings,
    merge_colors,
    save_settings,
)
from utils.themes import DARK

# 需要可注入 SETTINGS_PATH 的便利 —— 各测试用 monkeypatch 改模块属性
import utils.theme_settings as ts


@pytest.fixture(autouse=True)
def _tmp_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(ts, "SETTINGS_PATH", tmp_path / "user_theme.json")
    yield ts.SETTINGS_PATH


def test_color_slots_match_theme_keys():
    assert {k for k, _ in COLOR_SLOTS} == set(DARK)


def test_merge_override_wins_others_follow_base():
    merged = merge_colors(DARK, {"primary": "#ff5722"})
    assert merged["primary"] == "#ff5722"
    assert merged["bg_deep"] == DARK["bg_deep"]


def test_merge_ignores_unknown_key():
    merged = merge_colors(DARK, {"nope": "#000000"})
    assert "nope" not in merged


def test_load_missing_file_returns_defaults():
    assert load_settings() == DEFAULT_SETTINGS


def test_load_corrupt_json_returns_defaults(tmp_path, monkeypatch):
    p = tmp_path / "bad.json"
    p.write_text("{ not json", encoding="utf-8")
    monkeypatch.setattr(ts, "SETTINGS_PATH", p)
    assert load_settings() == DEFAULT_SETTINGS


def test_save_load_roundtrip():
    s = copy.deepcopy(DEFAULT_SETTINGS)
    s["colors"] = {"primary": "#ff5722"}
    s["background"]["window"] = {"image": r"D:\a.jpg", "opacity": 0.3}
    save_settings(s)
    loaded = load_settings()
    assert loaded["colors"] == {"primary": "#ff5722"}
    assert loaded["background"]["window"] == {"image": r"D:\a.jpg", "opacity": 0.3}
    assert loaded["dark"] is True


def test_normalize_clamps_opacity_and_keeps_valid(tmp_path, monkeypatch):
    p = tmp_path / "t.json"
    p.write_text(
        json.dumps({
            "dark": "not-a-bool",
            "colors": {"primary": "#ff5722", "bad": "zzz"},
            "background": {"window": {"opacity": 5}, "sidebar": {"opacity": -1}},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(ts, "SETTINGS_PATH", p)
    loaded = load_settings()
    assert loaded["dark"] is True
    assert loaded["colors"] == {"primary": "#ff5722"}
    assert loaded["background"]["window"]["opacity"] == 1.0
    assert loaded["background"]["sidebar"]["opacity"] == 0.0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`./venv/Scripts/python.exe -m pytest tests/test_theme_settings.py -v`
预期：FAIL（`ModuleNotFoundError: utils.theme_settings`）

- [ ] **步骤 3：编写实现**

```python
"""用户自定义主题设置 — 持久化与合并"""
import copy
import json
import os

from utils.config import PROJECT_ROOT

SETTINGS_PATH = PROJECT_ROOT / "config" / "user_theme.json"

# 可自定义颜色插槽：(键, 中文名)，键与 themes.DARK/LIGHT 完全一致
COLOR_SLOTS = [
    ("primary",      "主色"),
    ("primary_hi",   "主色高亮"),
    ("btn_text",     "按钮文字"),
    ("bg_deep",      "窗口背景"),
    ("bg_card",      "卡片背景"),
    ("bg_log",       "日志背景"),
    ("bg_input",     "输入框背景"),
    ("bg_sidebar",   "导航栏背景"),
    ("bg_tools",     "工具卡背景"),
    ("border_card",  "卡片边框"),
    ("border_ctrl",  "控件边框"),
    ("border_focus", "聚焦边框"),
    ("text_title",   "标题文字"),
    ("text_body",    "正文文字"),
    ("text_hint",    "次要文字"),
    ("text_dim",     "暗淡文字"),
    ("green",        "成功色"),
    ("red",          "错误色"),
    ("warning",      "警告色"),
    ("green_bg",     "成功底色"),
    ("red_bg",       "错误底色"),
    ("scrollbar",    "滚动条"),
    ("scroll_hover", "滚动条悬停"),
    ("drag_glow",    "拖拽辉光"),
]

DEFAULT_SETTINGS = {
    "dark": True,
    "colors": {},  # 覆盖色 {键: "#RRGGBB"}，仅存改过的
    "background": {
        "window":  {"image": None, "opacity": 0.5},
        "sidebar": {"image": None, "opacity": 0.8},
    },
}


def merge_colors(base: dict, overrides: dict) -> dict:
    """基础主题 + 用户覆盖 → 生效色字典。忽略未知键与空值。"""
    valid = {k for k, _ in COLOR_SLOTS}
    merged = dict(base)
    for k, v in (overrides or {}).items():
        if k in valid and v:
            merged[k] = v
    return merged


def _defaults() -> dict:
    return copy.deepcopy(DEFAULT_SETTINGS)


def load_settings() -> dict:
    """读取用户设置；文件缺失/损坏/结构非法一律回退默认结构。"""
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, ValueError):
        return _defaults()
    return _normalize(data)


def _normalize(data) -> dict:
    """补全缺失字段、剔除非法值，保证返回结构完整。"""
    out = _defaults()
    if not isinstance(data, dict):
        return out
    if isinstance(data.get("dark"), bool):
        out["dark"] = data["dark"]
    if isinstance(data.get("colors"), dict):
        for k, v in data["colors"].items():
            if isinstance(v, str) and v.startswith("#") and len(v) == 7:
                out["colors"][str(k)] = v.upper()
    bg = data.get("background")
    if isinstance(bg, dict):
        for region in ("window", "sidebar"):
            entry = bg.get(region)
            if not isinstance(entry, dict):
                continue
            if isinstance(entry.get("image"), str):
                out["background"][region]["image"] = entry["image"]
            op = entry.get("opacity")
            if isinstance(op, (int, float)):
                out["background"][region]["opacity"] = max(0.0, min(1.0, float(op)))
    return out


def save_settings(settings: dict) -> None:
    """原子写：临时文件 + os.replace。目录不存在时创建。"""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SETTINGS_PATH)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`./venv/Scripts/python.exe -m pytest tests/test_theme_settings.py -v`
预期：PASS（8 个测试）

- [ ] **步骤 5：Commit**

```bash
git add utils/theme_settings.py tests/test_theme_settings.py
git commit -m "feat: 主题设置持久化模块（load/save/merge/COLOR_SLOTS）"
```

---

### 任务 2：utils/themes.py — contentStack/sidebar 改透明

**文件：**
- 修改：`utils/themes.py`（build_stylesheet 两处）
- 测试：`tests/test_themes.py`

- [ ] **步骤 1：编写失败的测试**

```python
from utils.themes import DARK, build_stylesheet


def _segment(sheet: str, marker: str) -> str:
    i = sheet.find(marker)
    assert i >= 0, f"QSS 中找不到 {marker}"
    return sheet[i:i + 300]


def test_stylesheet_has_new_primary():
    assert "#1677cb" in build_stylesheet(DARK)


def test_content_stack_transparent():
    seg = _segment(build_stylesheet(DARK), "contentStack")
    assert "background-color: transparent" in seg


def test_sidebar_transparent():
    seg = _segment(build_stylesheet(DARK), "#sidebar")
    assert "background-color: transparent" in seg
```

- [ ] **步骤 2：运行测试验证失败**

运行：`./venv/Scripts/python.exe -m pytest tests/test_themes.py -v`
预期：后两个测试 FAIL（`#contentStack` 与 `QFrame#sidebar` 仍是实色）

- [ ] **步骤 3：修改 build_stylesheet**

在 `utils/themes.py` 的 `build_stylesheet` f-string 中改两处：

```python
/* 主内容区背景（实际底色由 AppBackground 背景层绘制） */
QStackedWidget#contentStack {{
    background-color: transparent;
}}
```

```python
#sidebar {{
    background-color: transparent;
}}
```

注意：sidebar 实现为 `SidebarBackground(AppBackground)`（QWidget 子类），故 QSS 用 `#sidebar` 按 objectName 选择；底色/图片/右侧 1px 边框全部由 `SidebarBackground.paintEvent` 绘制，这里只需保证无默认实色。

- [ ] **步骤 4：运行测试验证通过**

运行：`./venv/Scripts/python.exe -m pytest tests/test_themes.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add utils/themes.py tests/test_themes.py
git commit -m "style: QSS 中 contentStack/sidebar 改透明（背景层负责绘制底色）"
```

---

### 任务 3：gui/background.py — 背景绘制层

**文件：**
- 创建：`gui/background.py`
- 测试：`tests/test_background.py`

- [ ] **步骤 1：编写失败的测试**

```python
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QColor, QImage

from gui.background import AppBackground, SidebarBackground, _cover_rect


def test_cover_rect_landscape_smaller():
    r = _cover_rect(QSize(400, 200), QSize(200, 200))
    assert (r.x(), r.y(), r.width(), r.height()) == (-100, 0, 400, 200)


def test_cover_rect_square_fills_smaller():
    r = _cover_rect(QSize(100, 100), QSize(300, 200))
    assert (r.x(), r.y(), r.width(), r.height()) == (0, -50, 300, 300)


def test_cover_rect_zero_src():
    r = _cover_rect(QSize(0, 0), QSize(100, 100))
    assert r.width() == 0 and r.height() == 0


def test_app_background_with_image(app, tmp_path):
    p = tmp_path / "bg.jpg"
    img = QImage(64, 64, QImage.Format.Format_RGB32)
    img.fill(QColor("#ff0000"))
    assert img.save(str(p), "JPG")
    bg = AppBackground()
    assert bg.set_background("#0a0e17", str(p), 0.5) is True
    bg.resize(200, 100)
    bg.update()


def test_app_background_without_image(app):
    bg = AppBackground()
    assert bg.set_background("#0a0e17", None, 1.0) is False


def test_sidebar_background_draws_border(app):
    sb = SidebarBackground()
    sb.set_background("#0c0f15")
    sb.set_border("#334155")
    sb.resize(230, 600)
    sb.update()
```

- [ ] **步骤 2：运行测试验证失败**

运行：`./venv/Scripts/python.exe -m pytest tests/test_background.py -v`
预期：FAIL（`ModuleNotFoundError: gui.background`）

- [ ] **步骤 3：编写实现**

```python
"""窗口 / 导航栏背景层 — 纯色 + 可选图片（cover 等比铺满 + 透明度）"""
from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QWidget


def _cover_rect(src: QSize, dst: QSize) -> QRect:
    """将 src 按 cover 缩放铺满 dst 并居中（可越界），返回目标绘制区域。"""
    if src.width() <= 0 or src.height() <= 0 or dst.width() <= 0 or dst.height() <= 0:
        return QRect(0, 0, 0, 0)
    scale = max(dst.width() / src.width(), dst.height() / src.height())
    w = round(src.width() * scale)
    h = round(src.height() * scale)
    return QRect((dst.width() - w) // 2, (dst.height() - h) // 2, w, h)


def _load_image(path: str | None) -> QImage | None:
    if not path:
        return None
    img = QImage(path)
    return img if not img.isNull() else None


class AppBackground(QWidget):
    """应用背景层：先填底色，再按透明度绘制 cover 图片。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor("#0a0e17")
        self._image = None
        self._opacity = 1.0

    def set_background(self, color_hex: str, image_path: str | None = None,
                       opacity: float = 1.0) -> bool:
        """设置底色/图片/透明度。返回图片是否加载成功。"""
        self._color = QColor(color_hex)
        self._opacity = max(0.0, min(1.0, opacity))
        self._image = _load_image(image_path)
        self.update()
        return self._image is not None

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), self._color)
        if self._image is not None:
            p.setOpacity(self._opacity)
            rect = _cover_rect(self._image.size(), self.size())
            p.drawImage(rect, self._image)
            p.setOpacity(1.0)
        p.end()


class SidebarBackground(AppBackground):
    """导航栏背景层：在 AppBackground 之上追加右侧 1px 分隔线。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._border_color = QColor("#334155")

    def set_border(self, color_hex: str):
        self._border_color = QColor(color_hex)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setPen(self._border_color)
        x = self.width() - 1
        p.drawLine(x, 0, x, self.height())
        p.end()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`./venv/Scripts/python.exe -m pytest tests/test_background.py -v`
预期：PASS（6 个测试）

- [ ] **步骤 5：Commit**

```bash
git add gui/background.py tests/test_background.py
git commit -m "feat: 窗口/导航栏背景层（cover 缩放 + 透明度 + 分隔线）"
```

---

### 任务 4：gui/theme_settings_dialog.py + i18n 文案

**文件：**
- 创建：`gui/theme_settings_dialog.py`
- 修改：`utils/i18n.py`（新增文案键）
- 测试：`tests/test_theme_dialog.py`

- [ ] **步骤 1：向 utils/i18n.py 追加文案键**（`TEXTS` dict 内、`"theme.light"` 之后）

```python
    # ── 自定义主题对话框 ──
    "theme.open":                {"zh": "🎨 主题设置", "en": "🎨 Theme"},
    "theme.dialog.title":        {"zh": "自定义主题", "en": "Custom Theme"},
    "theme.dialog.background":   {"zh": "▧  背景设置", "en": "▧  Background"},
    "theme.dialog.window_bg":    {"zh": "窗口背景:", "en": "Window BG:"},
    "theme.dialog.sidebar_bg":   {"zh": "导航栏背景:", "en": "Sidebar BG:"},
    "theme.dialog.no_image":     {"zh": "（未设置，使用纯色）", "en": "(none — solid color)"},
    "theme.dialog.select_image": {"zh": "选择图片…", "en": "Select…"},
    "theme.dialog.remove_image": {"zh": "移除", "en": "Remove"},
    "theme.dialog.bad_image":    {"zh": "无法加载该图片，请选择有效的 jpg/png 文件。",
                                  "en": "Cannot load image. Choose a valid jpg/png."},
    "theme.dialog.colors":       {"zh": "🎨  自定义颜色", "en": "🎨  Custom Colors"},
    "theme.dialog.pick_color":   {"zh": "选择颜色", "en": "Choose Color"},
    "theme.dialog.reset_all":    {"zh": "↺  全部重置", "en": "↺  Reset All"},
    "theme.dialog.apply":        {"zh": "确定", "en": "OK"},
    "theme.dialog.cancel":       {"zh": "取消", "en": "Cancel"},
```

- [ ] **步骤 2：编写失败的测试**

```python
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog

from gui.theme_settings_dialog import ThemeSettingsDialog, _parse_hex
from utils.themes import DARK

_BG = {"window": {"image": None, "opacity": 0.5},
       "sidebar": {"image": None, "opacity": 0.8}}


def test_parse_hex_valid():
    assert _parse_hex("#ff5722") == "#FF5722"
    assert _parse_hex("ff5722") == "#FF5722"


def test_parse_hex_invalid():
    assert _parse_hex("#12345") is None
    assert _parse_hex("#gggggg") is None
    assert _parse_hex("") is None


def test_dialog_builds_all_rows(app):
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    assert len(dlg._color_rows) == len(DARK)


def test_dialog_collects_only_changed(app, monkeypatch):
    monkeypatch.setattr(QColorDialog, "getColor",
                        staticmethod(lambda *a, **k: QColor("#ff5722")))
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    dlg._color_rows["primary"]._on_pick()
    overrides = dlg._collect_colors()
    assert overrides == {"primary": "#FF5722"}


def test_dialog_hex_edit_syncs_swatch(app):
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    row = dlg._color_rows["primary"]
    row.hex_edit.setText("#112233")
    row.hex_edit.editingFinished.emit()
    assert row.current_hex() == "#112233"
    assert "#112233" in row.swatch.styleSheet()


def test_dialog_reset_all_clears_overrides(app, monkeypatch):
    monkeypatch.setattr(QColorDialog, "getColor",
                        staticmethod(lambda *a, **k: QColor("#ff5722")))
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    dlg._color_rows["primary"]._on_pick()
    dlg._on_reset_all()
    assert dlg._collect_colors() == {}


def test_dialog_result_data(app):
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    dlg._color_rows["green"].hex_edit.setText("#00ff00")
    dlg._color_rows["green"].hex_edit.editingFinished.emit()
    dlg._on_accept()
    data = dlg.result_data()
    assert data["colors"] == {"green": "#00FF00"}
    assert data["background"]["window"]["opacity"] == 0.5
    assert data["background"]["sidebar"]["image"] is None
```

- [ ] **步骤 3：运行测试验证失败**

运行：`./venv/Scripts/python.exe -m pytest tests/test_theme_dialog.py -v`
预期：FAIL（`ModuleNotFoundError: gui.theme_settings_dialog`）

- [ ] **步骤 4：编写实现**

```python
"""自定义主题设置对话框 — 背景设置 + 全部颜色键（hex 输入 + 色轮）"""
import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from utils.i18n import t
from utils.theme_settings import COLOR_SLOTS

_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def _parse_hex(text: str) -> str | None:
    """校验并规范化 hex；合法返回大写 #RRGGBB，否则 None。"""
    s = (text or "").strip()
    if _HEX_RE.fullmatch(s):
        return "#" + s.lstrip("#").upper()
    return None


class _ColorRow(QWidget):
    """单个颜色插槽：中文名 + 色块按钮(→色轮) + hex 输入框 + 单行重置。"""

    def __init__(self, key: str, zh_name: str, current_hex: str,
                 default_hex: str, parent=None):
        super().__init__(parent)
        self.key = key
        self._default_hex = default_hex.upper()
        self._hex = ""
        self._syncing = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(8)
        name = QLabel(zh_name)
        name.setMinimumWidth(96)
        lay.addWidget(name)
        self.swatch = QPushButton()
        self.swatch.setFixedSize(48, 24)
        self.swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.swatch.setToolTip(t("theme.dialog.pick_color"))
        self.swatch.clicked.connect(self._on_pick)
        lay.addWidget(self.swatch)
        self.hex_edit = QLineEdit()
        self.hex_edit.setMaxLength(7)
        self.hex_edit.setFixedWidth(90)
        self.hex_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hex_edit.textChanged.connect(self._on_hex_text)
        self.hex_edit.editingFinished.connect(self._on_hex_commit)
        lay.addWidget(self.hex_edit)
        self.reset_btn = QPushButton("↺")
        self.reset_btn.setFixedSize(28, 24)
        self.reset_btn.setToolTip("重置此项")
        self.reset_btn.clicked.connect(self._on_reset)
        lay.addWidget(self.reset_btn)
        lay.addStretch()
        self._set_hex(current_hex)

    def current_hex(self) -> str:
        return self._hex

    def _set_hex(self, hex_str: str):
        self._hex = hex_str.upper()
        self._syncing = True
        self.swatch.setStyleSheet(
            f"background-color: {self._hex}; border: 1px solid #888888; border-radius: 4px;")
        self.hex_edit.setText(self._hex)
        self._syncing = False

    def _on_hex_text(self, text: str):
        if self._syncing:
            return
        color = QColor(text if text.startswith("#") else "#" + text)
        if color.isValid():
            self._hex = color.name().upper()
            self.swatch.setStyleSheet(
                f"background-color: {self._hex}; border: 1px solid #888888; border-radius: 4px;")

    def _on_hex_commit(self):
        parsed = _parse_hex(self.hex_edit.text())
        if parsed is None:
            self.hex_edit.setStyleSheet("border: 1px solid #e5484d;")
            self.hex_edit.setText(self._hex)
        else:
            self.hex_edit.setStyleSheet("")
            self._set_hex(parsed)

    def _on_pick(self):
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor(self._hex), self, t("theme.dialog.pick_color"))
        if color.isValid():
            self._set_hex(color.name().upper())

    def _on_reset(self):
        self._set_hex(self._default_hex)


class _BackgroundRow(QWidget):
    """单个区域背景行：路径(只读) + 选择图片 + 移除 + 透明度滑块 + 百分比。"""

    def __init__(self, title: str, image_path: str | None, opacity: float, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setMinimumWidth(96)
        lay.addWidget(title_lbl)
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText(t("theme.dialog.no_image"))
        self.path_edit.setText(image_path or "")
        self.path_edit.setMinimumHeight(32)
        lay.addWidget(self.path_edit, 1)
        self.browse_btn = QPushButton(t("theme.dialog.select_image"))
        self.browse_btn.setMinimumHeight(32)
        self.browse_btn.clicked.connect(self._on_browse)
        lay.addWidget(self.browse_btn)
        self.remove_btn = QPushButton(t("theme.dialog.remove_image"))
        self.remove_btn.setMinimumHeight(32)
        self.remove_btn.setEnabled(bool(image_path))
        self.remove_btn.clicked.connect(self._on_remove)
        lay.addWidget(self.remove_btn)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(round(max(0.0, min(1.0, opacity)) * 100))
        self.slider.setFixedWidth(140)
        self.slider.valueChanged.connect(lambda v: self.pct_lbl.setText(f"{v}%"))
        lay.addWidget(self.slider)
        self.pct_lbl = QLabel(f"{self.slider.value()}%")
        self.pct_lbl.setFixedWidth(42)
        lay.addWidget(self.pct_lbl)
        lay.addStretch()

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("theme.dialog.select_image"), "",
            "Images (*.jpg *.jpeg *.png);;All files (*.*)")
        if path:
            if QImage(path).isNull():
                QMessageBox.warning(self, t("theme.dialog.title"),
                                    t("theme.dialog.bad_image"))
                return
            self.path_edit.setText(path)
            self.remove_btn.setEnabled(True)

    def _on_remove(self):
        self.path_edit.setText("")
        self.remove_btn.setEnabled(False)

    def image_path(self) -> str | None:
        p = self.path_edit.text().strip()
        return p or None

    def opacity(self) -> float:
        return self.slider.value() / 100.0


class ThemeSettingsDialog(QDialog):
    """返回 result_data(): {"colors": {覆盖色}, "background": {window/sidebar}}"""

    def __init__(self, base_colors: dict, overrides: dict, background: dict, parent=None):
        super().__init__(parent)
        self._base = base_colors
        self._result = None
        self.setWindowTitle(t("theme.dialog.title"))
        self.resize(600, 660)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        bg_title = QLabel(t("theme.dialog.background"))
        bg_title.setStyleSheet("font-weight: 700; font-size: 14px;")
        layout.addWidget(bg_title)

        win_bg = background.get("window", {})
        side_bg = background.get("sidebar", {})
        self.window_bg_row = _BackgroundRow(
            t("theme.dialog.window_bg"), win_bg.get("image"), win_bg.get("opacity", 1.0))
        self.sidebar_bg_row = _BackgroundRow(
            t("theme.dialog.sidebar_bg"), side_bg.get("image"), side_bg.get("opacity", 1.0))
        layout.addWidget(self.window_bg_row)
        layout.addWidget(self.sidebar_bg_row)

        colors_title = QLabel(t("theme.dialog.colors"))
        colors_title.setStyleSheet("font-weight: 700; font-size: 14px;")
        layout.addWidget(colors_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        col_lay = QVBoxLayout(container)
        col_lay.setContentsMargins(4, 4, 4, 4)
        col_lay.setSpacing(2)
        current = {**base_colors, **overrides}
        self._color_rows = {}
        for key, zh in COLOR_SLOTS:
            row = _ColorRow(key, zh,
                            current.get(key, base_colors.get(key, "#000000")),
                            base_colors.get(key, "#000000"))
            self._color_rows[key] = row
            col_lay.addWidget(row)
        col_lay.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.reset_all_btn = QPushButton(t("theme.dialog.reset_all"))
        self.reset_all_btn.clicked.connect(self._on_reset_all)
        layout.addWidget(self.reset_all_btn, alignment=Qt.AlignmentFlag.AlignRight)

        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton(t("theme.dialog.cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.cancel_btn)
        self.apply_btn = QPushButton(t("theme.dialog.apply"))
        self.apply_btn.setDefault(True)
        self.apply_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(self.apply_btn)
        layout.addLayout(btn_row)

    def _collect_colors(self) -> dict:
        out = {}
        for key, row in self._color_rows.items():
            cur = row.current_hex().upper()
            base = self._base.get(key, "#000000").upper()
            if cur != base:
                out[key] = cur
        return out

    def _on_reset_all(self):
        for row in self._color_rows.values():
            row._on_reset()

    def _on_accept(self):
        self._result = {
            "colors": self._collect_colors(),
            "background": {
                "window": {"image": self.window_bg_row.image_path(),
                           "opacity": self.window_bg_row.opacity()},
                "sidebar": {"image": self.sidebar_bg_row.image_path(),
                            "opacity": self.sidebar_bg_row.opacity()},
            },
        }
        self.accept()

    def result_data(self) -> dict:
        return self._result
```

- [ ] **步骤 5：运行测试验证通过**

运行：`./venv/Scripts/python.exe -m pytest tests/test_theme_dialog.py -v`
预期：PASS（7 个测试）

- [ ] **步骤 6：Commit**

```bash
git add gui/theme_settings_dialog.py utils/i18n.py tests/test_theme_dialog.py
git commit -m "feat: 自定义主题设置对话框（背景 + 24 色键 hex/色轮编辑）"
```

---

### 任务 5：gui/main_window.py — apply_theme 统一入口 + 背景层接线

**文件：**
- 修改：`gui/main_window.py`
- 测试：`tests/test_main_window.py`

- [ ] **步骤 1：编写失败的测试**

```python
from utils.themes import DARK
from utils.theme_settings import save_settings

import utils.theme_settings as ts


def _seed_settings(tmp_path, monkeypatch, colors=None, dark=True):
    monkeypatch.setattr(ts, "SETTINGS_PATH", tmp_path / "user_theme.json")
    save_settings({
        "dark": dark,
        "colors": colors or {},
        "background": {"window": {"image": None, "opacity": 0.5},
                       "sidebar": {"image": None, "opacity": 0.8}},
    })


def test_apply_theme_merges_overrides(app, tmp_path, monkeypatch):
    _seed_settings(tmp_path, monkeypatch, colors={"primary": "#ff5722"})
    from gui.main_window import MainWindow, _current_colors
    win = MainWindow()
    assert _current_colors["primary"] == "#ff5722"
    assert _current_colors["bg_deep"] == DARK["bg_deep"]
    assert win.sidebar_bg is not None
    assert win.theme_settings_btn is not None


def test_toggle_theme_persists_dark_flag(app, tmp_path, monkeypatch):
    _seed_settings(tmp_path, monkeypatch)
    from gui.main_window import MainWindow
    win = MainWindow()
    assert win._theme_is_dark is True
    win.toggle_theme()
    assert win._theme_is_dark is False
    assert ts.load_settings()["dark"] is False


def test_light_theme_applies_light_base(app, tmp_path, monkeypatch):
    _seed_settings(tmp_path, monkeypatch, colors={"primary": "#ff5722"}, dark=False)
    from gui.main_window import MainWindow, _current_colors
    win = MainWindow()
    assert _current_colors["bg_deep"] != DARK["bg_deep"]
    assert _current_colors["primary"] == "#ff5722"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`./venv/Scripts/python.exe -m pytest tests/test_main_window.py -v`
预期：FAIL（MainWindow 尚未接线，`_current_colors` 为 DARK、无 `sidebar_bg` 属性）

- [ ] **步骤 3：修改 gui/main_window.py**

导入区新增（`from utils.themes import ...` 一行附近）：

```python
from gui.background import AppBackground, SidebarBackground
from gui.theme_settings_dialog import ThemeSettingsDialog
from utils.theme_settings import load_settings, merge_colors, save_settings
```

`MainWindow.__init__` 改为：

```python
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self._theme_is_dark = bool(self.settings.get("dark", True))
        self.resize(1020, 720)
        self.setMinimumSize(860, 600)
        self.setup_ui()
        self.apply_theme()
        self.check_tools()
        self.retranslate()
```

`setup_ui` 中：`central = QWidget()` → `central = AppBackground()`，并保存 `self.central_bg = central`；`sidebar = QFrame()` → `sidebar = SidebarBackground()`，保存 `self.sidebar_bg = sidebar`（保留 `setObjectName("sidebar")`，由类内部完成）。切换按钮行在 `self.theme_btn` 前插入设置按钮：

```python
        self.theme_settings_btn = QPushButton()
        self.theme_settings_btn.setObjectName("toolbarBtn")
        self.theme_settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_settings_btn.clicked.connect(self.open_theme_settings)

        toggle_row.addWidget(self.theme_settings_btn)
```

新增方法（替代 `toggle_theme` 内的旧样式代码）：

```python
    # ── 主题应用（唯一入口） ──
    def apply_theme(self):
        global _current_colors
        base = DARK if self._theme_is_dark else LIGHT
        colors = merge_colors(base, self.settings.get("colors", {}))
        _current_colors = colors
        sheet = build_stylesheet(colors)
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        app.setStyleSheet(sheet)
        # 同步 palette
        from PyQt6.QtGui import QColor, QPalette
        p = app.palette()
        p.setColor(QPalette.ColorRole.Window, QColor(colors['bg_deep']))
        p.setColor(QPalette.ColorRole.WindowText, QColor(colors['text_body']))
        p.setColor(QPalette.ColorRole.Base, QColor(colors['bg_input']))
        p.setColor(QPalette.ColorRole.Text, QColor(colors['text_body']))
        p.setColor(QPalette.ColorRole.Button, QColor(colors['border_ctrl']))
        p.setColor(QPalette.ColorRole.ButtonText, QColor(colors['text_body']))
        app.setPalette(p)
        self._update_theme_widgets(colors)
        self._apply_background()
        self.retranslate()
        self.repaint()
        app.processEvents()

    def _apply_background(self):
        bg = self.settings.get("background", {})
        win = bg.get("window", {})
        side = bg.get("sidebar", {})
        c = _current_colors
        self.central_bg.set_background(c["bg_deep"], win.get("image"),
                                       float(win.get("opacity", 1.0)))
        self.sidebar_bg.set_background(c["bg_sidebar"], side.get("image"),
                                       float(side.get("opacity", 1.0)))
        self.sidebar_bg.set_border(c["border_ctrl"])

    def toggle_theme(self):
        self._theme_is_dark = not self._theme_is_dark
        self.settings["dark"] = self._theme_is_dark
        save_settings(self.settings)
        self.apply_theme()

    def open_theme_settings(self):
        base = DARK if self._theme_is_dark else LIGHT
        dlg = ThemeSettingsDialog(base, self.settings.get("colors", {}),
                                  self.settings.get("background", {}), self)
        if dlg.exec():
            data = dlg.result_data()
            self.settings["colors"] = data["colors"]
            self.settings["background"] = data["background"]
            save_settings(self.settings)
            self.apply_theme()
```

`_update_theme_widgets` 中页面背景行改为透明（背景层负责底色）：

```python
            page.setStyleSheet("background-color: transparent;")
```

`retranslate` 中（`self.lang_btn.setText(...)` 之后）加：

```python
        self.theme_settings_btn.setText(t("theme.open"))
```

- [ ] **步骤 4：运行测试验证通过**

运行：`./venv/Scripts/python.exe -m pytest tests/test_main_window.py -v`
预期：PASS（3 个测试）

- [ ] **步骤 5：Commit**

```bash
git add gui/main_window.py tests/test_main_window.py
git commit -m "feat: apply_theme 统一入口 + 背景层接线 + 主题设置入口"
```

---

### 任务 6：集成验证 + 打包

**文件：**
- 修改：无（`main.py` 保留首帧兜底样式，MainWindow 启动即覆盖）

- [ ] **步骤 1：全量测试**

运行：`./venv/Scripts/python.exe -m pytest tests/ -v`
预期：全部 PASS（主题 settings 8 + themes 3 + background 6 + dialog 7 + main_window 3）

- [ ] **步骤 2：ruff 静态检查**

运行：`./venv/Scripts/python.exe -m ruff check utils/ gui/ tests/ main.py`
预期：无错误（若 ruff 未安装则先 `./venv/Scripts/python.exe -m pip install ruff`）

- [ ] **步骤 3：开发模式冒烟（离线 GUI，不跑事件循环）**

运行：
```bash
./venv/Scripts/python.exe -c "
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow, _current_colors
app = QApplication([])
w = MainWindow()
print('colors primary =', _current_colors['primary'])
print('sidebar_bg =', type(w.sidebar_bg).__name__)
print('settings_btn =', w.theme_settings_btn.text())
"
```
预期：三行正常输出，无异常。

- [ ] **步骤 4：重新打包 + 自检**（用户视觉确认后执行）

```bash
rm -rf build dist/Transallum
./venv/Scripts/python.exe -m PyInstaller transallum.spec --noconfirm
# 恢复外部工具与模型 junction（tools/ + models junction，参照项目历史做法）
./venv/Scripts/python.exe -c "from utils.config import detect_gpu; print('gpu ok')"
./dist/Transallum/Transallum.exe --selftest-gpu
```

预期：selftest exit 0，`logs/selftest.log` 全步骤通过。

- [ ] **步骤 5：提交计划与设计收尾**

```bash
git add docs/superpowers/plans/2026-08-20-custom-theme.md docs/superpowers/specs/2026-08-20-custom-theme-design.md
git commit -m "docs: 自定义主题实现计划 + 规格色键数修正(24)"
```

- [ ] **步骤 6：交付报告**

向用户报告：功能入口（侧栏「🎨 主题设置」）、测试结果、打包状态、请用户在开发模式或打包版验证清单（改色即时生效/重启保留/窗口与导航栏分别换背景/透明度调整/深浅切换后覆盖色仍生效）。

---

## 自检

- **规格覆盖度：** 背景独立自定义（任务 3+4+5）、全部色键（任务 1+4）、hex+色轮（任务 4 QColorDialog 兼具）、覆盖叠加（任务 5 apply_theme）、持久化（任务 1+5）、打包（任务 6）。无遗漏。
- **占位符扫描：** 所有步骤含实际代码；无 TODO/“适当处理”。`main.py` 明确“无需改动”。
- **类型一致性：** `set_background(color, image_path, opacity) -> bool` 在 gui/background.py 定义、main_window 调用、测试断言一致；`ThemeSettingsDialog(base_colors, overrides, background)` 与 `result_data()` 返回结构在任务 4/5 一致；`_cover_rect` 在 background.py 与测试一致。
