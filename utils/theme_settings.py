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
                out["colors"][str(k)] = v
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
