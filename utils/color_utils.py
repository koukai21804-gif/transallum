"""颜色值解析与合成：透明颜色统一用 CSS rgba(r,g,b,a) 表示（a∈[0,1]，与 QSS 兼容）。

不透明白点用大写 #RRGGBB 表示（缺省 alpha=1.0）；带透明度回退 rgba(r,g,b,a)。
主题设置里每个可编辑颜色都可带 0-100% 透明度，此模块负责双向转换与规范化。
"""
import re

_HEX6 = re.compile(r"^#?([0-9a-fA-F]{6})$")
_HEX3 = re.compile(r"^#?([0-9a-fA-F]{3})$")
_RGBA = re.compile(
    r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*"
    r"(?:,\s*([\d.]+)\s*)?\)",
    re.IGNORECASE,
)


def split_color(value: str) -> tuple[int, int, int, float] | None:
    """把 #RRGGBB / #RGB / rgb(r,g,b) / rgba(r,g,b,a) 拆成 (r, g, b, alpha)。

    alpha∈[0,1]（不透明白点返回 1.0）；非法返回 None。
    通道值钳制到 [0,255]，alpha 钳制到 [0,1]。
    """
    s = (value or "").strip()
    m = _HEX6.match(s)
    if m:
        h = m.group(1)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0
    m = _HEX3.match(s)
    if m:
        h = m.group(1)
        return int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16), 1.0
    m = _RGBA.match(s)
    if m:
        r = min(255, int(m.group(1)))
        g = min(255, int(m.group(2)))
        b = min(255, int(m.group(3)))
        alpha = float(m.group(4)) if m.group(4) is not None else 1.0
        return r, g, b, max(0.0, min(1.0, alpha))
    return None


def make_color(r: int, g: int, b: int, alpha: float) -> str:
    """合成颜色串：alpha 四舍五入到 0.01 后 <1 返回 rgba(r,g,b,a)，否则返回大写 #RRGGBB。"""
    r, g, b = int(r) & 255, int(g) & 255, int(b) & 255
    alpha = max(0.0, min(1.0, float(alpha)))
    if round(alpha, 2) >= 1.0:
        return f"#{r:02X}{g:02X}{b:02X}"
    a = f"{alpha:.2f}".rstrip("0").rstrip(".")
    return f"rgba({r}, {g}, {b}, {a})"


def alpha_of(value: str) -> float:
    """取颜色透明度；非法按 1.0。"""
    sp = split_color(value)
    return sp[3] if sp else 1.0


def normalize_color(value: str) -> str | None:
    """把任意合法颜色规范化为展示形式；非法返回 None。"""
    sp = split_color(value)
    return make_color(*sp) if sp is not None else None
