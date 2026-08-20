import copy
import json

import pytest

# 需要可注入 SETTINGS_PATH 的便利 —— 各测试用 monkeypatch 改模块属性
import utils.theme_settings as ts
from utils.theme_settings import (
    COLOR_SLOTS,
    DEFAULT_SETTINGS,
    load_settings,
    merge_colors,
    save_settings,
)
from utils.themes import DARK


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
