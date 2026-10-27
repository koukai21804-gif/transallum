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
from utils.themes import DARK, LIGHT


@pytest.fixture(autouse=True)
def _tmp_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(ts, "SETTINGS_PATH", tmp_path / "user_theme.json")
    yield ts.SETTINGS_PATH


def test_color_slots_match_theme_keys():
    """COLOR_SLOTS 覆盖主题全部色键；font_family 是字体名而非颜色，不开放自定义。"""
    slots = {k for k, _ in COLOR_SLOTS}
    assert set(DARK) - slots == {"font_family"}
    assert set(LIGHT) - slots == {"font_family"}


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
    s["themes"]["dark"]["colors"] = {"primary": "#ff5722"}
    s["themes"]["dark"]["background"]["window"] = {"image": r"D:\a.jpg", "opacity": 0.3}
    save_settings(s)
    loaded = load_settings()
    assert loaded["themes"]["dark"]["colors"] == {"primary": "#ff5722"}
    assert loaded["themes"]["dark"]["background"]["window"] == {
        "image": r"D:\a.jpg", "opacity": 0.3
    }
    # 深浅两套方案互不共享：浅色保持默认
    assert loaded["themes"]["light"]["colors"] == {}
    assert loaded["dark"] is True


def test_normalize_clamps_opacity_and_keeps_valid(tmp_path, monkeypatch):
    p = tmp_path / "t.json"
    p.write_text(
        json.dumps({
            "dark": "not-a-bool",
            "themes": {
                "dark": {
                    "colors": {"primary": "#ff5722", "bad": "zzz"},
                    "background": {"window": {"opacity": 5}, "sidebar": {"opacity": -1}},
                }
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(ts, "SETTINGS_PATH", p)
    loaded = load_settings()
    assert loaded["dark"] is True
    assert loaded["themes"]["dark"]["colors"] == {"primary": "#ff5722"}
    assert loaded["themes"]["dark"]["background"]["window"]["opacity"] == 1.0
    assert loaded["themes"]["dark"]["background"]["sidebar"]["opacity"] == 0.0


def test_load_legacy_flat_settings_migrates_to_both_themes(tmp_path, monkeypatch):
    """旧扁平结构（colors/background 挂根上、深浅共用）自动迁移为按主题拆分。"""
    p = tmp_path / "legacy.json"
    p.write_text(
        json.dumps({
            "dark": True,
            "colors": {"primary": "#ff5722"},
            "background": {"window": {"image": r"D:\a.jpg", "opacity": 0.3}},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(ts, "SETTINGS_PATH", p)
    loaded = load_settings()
    for name in ("dark", "light"):
        prof = loaded["themes"][name]
        assert prof["colors"] == {"primary": "#ff5722"}
        assert prof["background"]["window"] == {"image": r"D:\a.jpg", "opacity": 0.3}
