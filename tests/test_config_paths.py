"""config 路径与模型判定 helper 的单元测试。

覆盖要点：
- user_data_dir()/settings_path() 在冻结态（安装版）重定向到 %APPDATA%\\Transallum，
  开发态回落到 PROJECT_ROOT。
- is_model_installed() 只认随包目录（+冻结态用户已下载目录），不含开发机共享回退。
- resolve_whisper_model() 冻结态额外探测用户可写模型目录。
"""
import sys

from utils import config


# ── user_data_dir / settings_path ──

def test_user_data_dir_dev(monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert config.user_data_dir() == config.PROJECT_ROOT


def test_user_data_dir_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    ap = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(ap))
    assert config.user_data_dir() == ap / "Transallum"


def test_settings_path_dev(monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert config.settings_path() == config.PROJECT_ROOT / "config" / "user_theme.json"


def test_settings_path_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    ap = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(ap))
    expected = ap / "Transallum" / "config" / "user_theme.json"
    assert config.settings_path() == expected


# ── is_model_installed ──

def test_is_model_installed_bundled(monkeypatch, tmp_path):
    """只认随包目录里存在 model.bin 的模型。"""
    sniff = tmp_path / "models" / "whisper"
    (sniff / "large-v3").mkdir(parents=True)
    (sniff / "large-v3" / "model.bin").write_bytes(b"x")
    monkeypatch.setattr(config, "WHISPER_MODELS_DIR", sniff)
    assert config.is_model_installed("large-v3") is True
    assert config.is_model_installed("tiny") is False


def test_is_model_installed_user_dir_frozen(monkeypatch, tmp_path):
    """冻结态：联网补充下载到 %APPDATA%\\Transallum 的模型也算已安装。"""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    ap = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(ap))
    bundled = tmp_path / "bundled"
    bundled.mkdir()
    monkeypatch.setattr(config, "WHISPER_MODELS_DIR", bundled)
    # 下载到用户目录的 medium
    (ap / "Transallum" / "models" / "whisper" / "medium").mkdir(parents=True)
    (ap / "Transallum" / "models" / "whisper" / "medium" / "model.bin").write_bytes(b"x")
    assert config.is_model_installed("medium") is True
    assert config.is_model_installed("tiny") is False


def test_resolve_whisper_model_frozen_user_dir(monkeypatch, tmp_path):
    """冻结态 resolve_whisper_model 能命中用户可写目录的模型。"""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    ap = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(ap))
    bundled = tmp_path / "bundled"
    bundled.mkdir()
    monkeypatch.setattr(config, "WHISPER_MODELS_DIR", bundled)
    # 避免外部共享目录干扰：指向不存在的路径
    monkeypatch.setattr(config, "_SHARED_MODELS_DIR", tmp_path / "no_such_shared")
    md = ap / "Transallum" / "models" / "whisper" / "small"
    md.mkdir(parents=True)
    (md / "model.bin").write_bytes(b"x")
    assert config.resolve_whisper_model("small") == str(md)


# ── theme_settings.SETTINGS_PATH 与 config.settings_path()/dir 一致 ──

def test_theme_settings_path_matches_config(monkeypatch):
    from utils import theme_settings
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert theme_settings.SETTINGS_PATH == config.settings_path()
