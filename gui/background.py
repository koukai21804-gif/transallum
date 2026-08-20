"""窗口 / 导航栏背景层 — 纯色 + 可选图片（cover 等比铺满 + 透明度）"""
from PyQt6.QtCore import QRect, QSize
from PyQt6.QtGui import QColor, QImage, QPainter
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
