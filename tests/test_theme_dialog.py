from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog

from gui.theme_settings_dialog import ThemeSettingsDialog, _parse_hex
from utils.theme_settings import COLOR_SLOTS
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
    # 每一可编辑颜色插槽对应一行（font_family 非颜色，不在 COLOR_SLOTS）
    assert len(dlg._color_rows) == len(COLOR_SLOTS)


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
    assert row.current_value() == "#112233"
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


# ── rgba 半透明基色（green_bg/red_bg/drag_glow）—— 现均支持 RGB+透明度编辑 ──

def test_rgba_row_hex_shows_rgb_and_slider_alpha(app):
    """rgba 基色行：hex 框启用并显示 RGB，透明度滑块显示基色 alpha。"""
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    row = dlg._color_rows["green_bg"]
    assert row.hex_edit.isEnabled()
    assert _parse_hex(row.hex_edit.text()) == "#4ADE80"
    assert row.alpha_slider.value() == 8          # rgba(74,222,128,0.08) → 8%
    assert row.pct_lbl.text() == "8%"


def test_rgba_row_pick_keeps_fractional_alpha(app, monkeypatch):
    """rgba 行经色块选色改 RGB，但保留原有透明度 → rgba 覆盖被收集。"""
    monkeypatch.setattr(QColorDialog, "getColor",
                        staticmethod(lambda *a, **k: QColor("#ff5722")))
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    row = dlg._color_rows["green_bg"]
    row._on_pick()
    assert row.alpha_slider.value() == 8          # 透明度不变
    assert row.current_value() == "rgba(255, 87, 34, 0.08)"
    assert _parse_hex(row.hex_edit.text()) == "#FF5722"
    assert dlg._collect_colors() == {"green_bg": "rgba(255, 87, 34, 0.08)"}


def test_rgba_row_slider_to_opaque_gives_hex(app):
    """把 rgba 行透明度拉到 100% → 合成纯 hex，被收集。"""
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    row = dlg._color_rows["green_bg"]
    row.alpha_slider.setValue(100)
    assert row.current_value() == "#4ADE80"
    assert dlg._collect_colors() == {"green_bg": "#4ADE80"}


def test_rgba_row_reset_returns_base(app, monkeypatch):
    """重置 rgba 行回到基色 → RGB 与透明度都回到基色，不收集。"""
    monkeypatch.setattr(QColorDialog, "getColor",
                        staticmethod(lambda *a, **k: QColor("#ff5722")))
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    row = dlg._color_rows["drag_glow"]
    row._on_pick()
    assert row.current_value() != None
    row._on_reset()
    assert row.alpha_slider.value() == 8
    assert row.current_value() == "rgba(22, 119, 203, 0.08)"
    assert dlg._collect_colors() == {}


def test_rgba_rows_untouched_not_collected(app):
    """未触碰的 rgba 行（cur==base）不进入覆盖集。"""
    dlg = ThemeSettingsDialog(DARK, {}, _BG)
    overrides = dlg._collect_colors()
    for key in ("green_bg", "red_bg", "drag_glow"):
        assert key not in overrides
