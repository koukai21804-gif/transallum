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
