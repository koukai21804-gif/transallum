"""用户自定义主题设置 — 持久化与合并

深色/浅色为两套完全独立的设置方案（字体、背景、自定义颜色均互不共享）。
存储结构：settings["themes"]["dark"|"light"] = {"colors", "background"}。
颜色值可为 #RRGGBB（不透明）或 rgba(r,g,b,a)（带 0-100% 透明度）。
"""
import copy
import json
import os

from utils.color_utils import split_color
from utils.config import settings_path

# 冻结态（安装版）写到 %APPDATA%\\Transallum\\config\\，开发态写 PROJECT_ROOT\\config\\。
# 安装到 Program Files（只读）后靠此重定向避免写权限崩溃。
SETTINGS_PATH = settings_path()

# 可自定义颜色插槽：(键, 中文名)，键与 themes.DARK/LIGHT 完全一致
COLOR_SLOTS = [
    ("primary",      "主色"),
    ("primary_hi",   "主色高亮"),
    ("page_title",   "页面标题/品牌名"),
    ("btn_text",     "按钮文字"),
    ("bg_deep",      "窗口背景"),
    ("bg_card",      "卡片背景"),
    ("chip_bg",      "分栏小标题底色"),
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


def _default_theme_profile() -> dict:
    """单个主题的独立方案：自定义颜色 + 背景（深/浅互不共享）。"""
    return {
        "colors": {},  # 覆盖色 {键: "#RRGGBB"}，仅存改过的
        "background": {
            "window":  {"image": None, "opacity": 0.5},
            "sidebar": {"image": None, "opacity": 0.8},
        },
    }


DEFAULT_SETTINGS = {
    "dark": True,
    "themes": {
        "dark":  _default_theme_profile(),
        "light": _default_theme_profile(),
    },
}


def _defaults() -> dict:
    return copy.deepcopy(DEFAULT_SETTINGS)


def merge_colors(base: dict, overrides: dict) -> dict:
    """基础主题 + 用户覆盖 → 生效色字典。忽略未知键与空值。"""
    valid = {k for k, _ in COLOR_SLOTS}
    merged = dict(base)
    for k, v in (overrides or {}).items():
        if k in valid and v:
            merged[k] = v
    return merged


def theme_profile(settings: dict, is_dark: bool) -> dict:
    """取出指定主题的 {colors, background} 方案（就地可改，随 save_settings 持久化）。

    深色/浅色各自独立：改浅色背景或颜色不会影响深色，反之亦然。
    """
    name = "dark" if is_dark else "light"
    themes = settings.setdefault("themes", {})
    prof = themes.get(name)
    if not isinstance(prof, dict):
        prof = themes[name] = {}
    prof.setdefault("colors", {})
    prof.setdefault("background", {})
    prof["background"].setdefault("window", {"image": None, "opacity": 0.5})
    prof["background"].setdefault("sidebar", {"image": None, "opacity": 0.8})
    return prof


def _clean_colors(raw) -> dict:
    """只保留合法颜色覆盖值（#RRGGBB 或 rgba()），原样保留不改变大小写。"""
    out = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, str) and split_color(v) is not None:
                out[str(k)] = v
    return out


def _clean_background(raw) -> dict:
    """规范化背景结构，剔除非法值。"""
    out = {"window": {"image": None, "opacity": 0.5},
           "sidebar": {"image": None, "opacity": 0.8}}
    if isinstance(raw, dict):
        for region in ("window", "sidebar"):
            entry = raw.get(region)
            if not isinstance(entry, dict):
                continue
            if isinstance(entry.get("image"), str):
                out[region]["image"] = entry["image"]
            op = entry.get("opacity")
            if isinstance(op, (int, float)):
                out[region]["opacity"] = max(0.0, min(1.0, float(op)))
    return out


def load_settings() -> dict:
    """读取用户设置；文件缺失/损坏/结构非法一律回退默认结构。

    兼容旧版扁平结构（colors/background 挂在根上、深浅共用）：
    自动迁移为按主题拆分，旧值同时赋给深/浅两套方案。
    """
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, ValueError):
        return _defaults()
    return _normalize(data)


def _normalize(data) -> dict:
    """补全缺失字段、剔除非法值，保证返回结构完整（按主题拆分）。"""
    out = _defaults()
    if not isinstance(data, dict):
        return out
    if isinstance(data.get("dark"), bool):
        out["dark"] = data["dark"]
    themes = data.get("themes")
    if isinstance(themes, dict):
        for name in ("dark", "light"):
            prof = themes.get(name)
            if not isinstance(prof, dict):
                continue
            if isinstance(prof.get("colors"), dict):
                out["themes"][name]["colors"] = _clean_colors(prof["colors"])
            if isinstance(prof.get("background"), dict):
                out["themes"][name]["background"] = _clean_background(prof["background"])
    else:
        # 旧扁平结构迁移：colors/background 曾深浅共用 → 同时赋给两套方案
        colors = _clean_colors(data.get("colors"))
        bg = _clean_background(data.get("background"))
        out["themes"]["dark"]["colors"] = dict(colors)
        out["themes"]["light"]["colors"] = dict(colors)
        out["themes"]["dark"]["background"] = bg
        out["themes"]["light"]["background"] = copy.deepcopy(bg)
    return out


def save_settings(settings: dict) -> None:
    """原子写：临时文件 + os.replace。目录不存在时创建。"""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SETTINGS_PATH)
