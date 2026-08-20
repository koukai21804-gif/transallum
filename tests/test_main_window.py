import gui.main_window as mw
import utils.theme_settings as ts
from utils.theme_settings import save_settings
from utils.themes import DARK


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
    win = mw.MainWindow()
    assert mw._current_colors["primary"] == "#ff5722"
    assert mw._current_colors["bg_deep"] == DARK["bg_deep"]
    assert win.sidebar_bg is not None
    assert win.theme_settings_btn is not None


def test_toggle_theme_persists_dark_flag(app, tmp_path, monkeypatch):
    _seed_settings(tmp_path, monkeypatch)
    win = mw.MainWindow()
    assert win._theme_is_dark is True
    win.toggle_theme()
    assert win._theme_is_dark is False
    assert ts.load_settings()["dark"] is False


def test_light_theme_applies_light_base(app, tmp_path, monkeypatch):
    _seed_settings(tmp_path, monkeypatch, colors={"primary": "#ff5722"}, dark=False)
    mw.MainWindow()
    assert mw._current_colors["bg_deep"] != DARK["bg_deep"]
    assert mw._current_colors["primary"] == "#ff5722"
