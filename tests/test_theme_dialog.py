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
