"""自定义主题设置对话框 — 背景设置 + 全部颜色键（hex + 色轮 + 透明度 0-100%）"""
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

from utils.color_utils import make_color, normalize_color, split_color
from utils.i18n import t
from utils.theme_settings import COLOR_SLOTS

_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def _parse_hex(text: str) -> str | None:
    """校验并规范化 hex；合法返回大写 #RRGGBB，否则 None。"""
    s = (text or "").strip()
    if _HEX_RE.fullmatch(s):
        return "#" + s.lstrip("#").upper()
    return None


def _to_qcolor(value: str) -> QColor:
    """把 #RRGGBB / rgb() / rgba() 转成 QColor（忽略透明度，供色轮初始色）。

    QColor 的字符串构造不解析 CSS rgba()（实测返回 invalid），故手动拆 RGB。
    """
    sp = split_color(value)
    if sp is None:
        return QColor()
    return QColor(sp[0], sp[1], sp[2])


class _ColorRow(QWidget):
    """单个颜色插槽：中文名 + 色块(→色轮) + hex(RGB) + 透明度滑块(0-100%) + 重置。

    颜色值由独立的 RGB 与透明度合成：hex/色轮只改 RGB，滑块只改透明度，
    _value 存合成后的颜色串（不透明白点为 #RRGGBB，否则 rgba(r,g,b,a)）。
    """

    def __init__(self, key: str, zh_name: str, current: str, default: str, parent=None):
        super().__init__(parent)
        self.key = key
        self._default = default
        self._rgb = (0, 0, 0)
        self._alpha = 1.0
        self._value = ""
        self._syncing = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(6)
        name = QLabel(zh_name)
        name.setMinimumWidth(88)
        lay.addWidget(name)
        self.swatch = QPushButton()
        self.swatch.setFixedSize(44, 22)
        self.swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.swatch.setToolTip(t("theme.dialog.pick_color"))
        self.swatch.clicked.connect(self._on_pick)
        lay.addWidget(self.swatch)
        self.hex_edit = QLineEdit()
        self.hex_edit.setMaxLength(7)
        self.hex_edit.setFixedWidth(78)
        self.hex_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hex_edit.textChanged.connect(self._on_hex_text)
        self.hex_edit.editingFinished.connect(self._on_hex_commit)
        lay.addWidget(self.hex_edit)
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setFixedWidth(96)
        self.alpha_slider.setToolTip(t("theme.dialog.alpha_hint"))
        self.alpha_slider.valueChanged.connect(self._on_alpha)
        lay.addWidget(self.alpha_slider)
        self.pct_lbl = QLabel("100%")
        self.pct_lbl.setFixedWidth(38)
        lay.addWidget(self.pct_lbl)
        self.reset_btn = QPushButton("↺")
        self.reset_btn.setFixedSize(24, 22)
        self.reset_btn.setToolTip("重置此项")
        self.reset_btn.clicked.connect(self._on_reset)
        lay.addWidget(self.reset_btn)
        lay.addStretch()
        self._set_value(current)

    def current_value(self) -> str:
        return self._value

    def _set_value(self, value: str):
        """写入当前颜色串：拆成 RGB + 透明度，同步色块/hex/滑块。"""
        sp = split_color(value)
        if sp is None:
            sp = (0, 0, 0, 1.0)
        r, g, b, alpha = sp
        self._syncing = True
        self._rgb = (r, g, b)
        self._alpha = alpha
        self._value = normalize_color(value) or make_color(r, g, b, alpha)
        self.hex_edit.setEnabled(True)
        self.hex_edit.setPlaceholderText("")
        self.hex_edit.setText(f"#{r:02X}{g:02X}{b:02X}")
        self.alpha_slider.setValue(round(alpha * 100))
        self.pct_lbl.setText(f"{round(alpha * 100)}%")
        self._refresh_swatch()
        self._syncing = False

    def _refresh_swatch(self):
        self.swatch.setStyleSheet(
            f"background-color: {self._value}; border: 1px solid #888888; border-radius: 4px;")

    def _commit(self):
        """由当前 RGB + 透明度合成颜色串并刷新色块。"""
        self._value = make_color(*self._rgb, self._alpha)
        self._refresh_swatch()

    def _on_hex_text(self, text: str):
        if self._syncing:
            return
        q = QColor(text if text.startswith("#") else "#" + text)
        if q.isValid():
            self._rgb = (q.red(), q.green(), q.blue())
            self._commit()

    def _on_hex_commit(self):
        parsed = _parse_hex(self.hex_edit.text())
        if parsed is None:
            self.hex_edit.setStyleSheet("border: 1px solid #e5484d;")
            r, g, b = self._rgb
            self.hex_edit.setText(f"#{r:02X}{g:02X}{b:02X}")
        else:
            self.hex_edit.setStyleSheet("")
            self._rgb = (int(parsed[1:3], 16), int(parsed[3:5], 16), int(parsed[5:7], 16))
            self._commit()

    def _on_alpha(self, v: int):
        if self._syncing:
            return
        self._alpha = v / 100.0
        self.pct_lbl.setText(f"{v}%")
        self._commit()

    def _on_pick(self):
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor(*self._rgb), self, t("theme.dialog.pick_color"))
        if color.isValid():
            self._rgb = (color.red(), color.green(), color.blue())
            self._syncing = True
            self.hex_edit.setText(f"#{color.red():02X}{color.green():02X}{color.blue():02X}")
            self._syncing = False
            self._commit()

    def _on_reset(self):
        self._set_value(self._default)


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
        self.resize(660, 680)
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
            cur = row.current_value()
            base = normalize_color(self._base.get(key, "#000000")) or "#000000"
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
