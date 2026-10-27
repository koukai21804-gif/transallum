"""应用配置和外部工具检测"""
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _detect_project_root() -> Path:
    """检测项目根目录（开发 & 打包均适用）"""
    # 方式1: PyInstaller 打包 → exe 所在目录
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    # 方式2: 开发模式 → 本文件向上两级
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _detect_project_root()
TOOLS_DIR = PROJECT_ROOT / "tools"


def user_data_dir() -> Path:
    """运行时用户可写数据目录：冻结态 %APPDATA%\\Transallum，开发态 PROJECT_ROOT。

    安装到 Program Files（只读）后，一切运行时写操作（主题设置/日志/模型下载）
    都须落在用户可写的这个目录，否则会因权限崩溃。
    """
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA", str(Path.home())))
        return base / "Transallum"
    return PROJECT_ROOT


def settings_path() -> Path:
    """用户主题设置路径：冻结态 %APPDATA%\\Transallum\\config\\user_theme.json，
    开发态 PROJECT_ROOT\\config\\user_theme.json。"""
    return user_data_dir() / "config" / "user_theme.json"


# ── Whisper 模型本地目录 ──
WHISPER_MODELS_DIR = PROJECT_ROOT / "models" / "whisper"
# 可选共享模型目录（指向 models/whisper 级目录，含 <size>/model.bin）：
# 仅当设置环境变量 TRANSALLUM_SHARED_MODELS 时参与查找，供开发机在
# 多个工作副本间共享大模型；普通用户无需设置。
_SM_ENV = os.environ.get("TRANSALLUM_SHARED_MODELS")
_SHARED_MODELS_DIR = Path(_SM_ENV) if _SM_ENV else None


def local_model_dirs(model_size: str) -> list:
    """本地（随包分发或已下载）模型候选目录，首个为随包内置目录。

    刻意不含共享目录 _SHARED_MODELS_DIR——打包版不应据此把未随包的
    小模型误判为已安装（开发流程由 resolve_whisper_model 兜底，不受影响）。
    """
    dirs = [WHISPER_MODELS_DIR / model_size]
    if getattr(sys, "frozen", False):
        dirs.append(user_data_dir() / "models" / "whisper" / model_size)
    return dirs


def is_model_installed(model_size: str) -> bool:
    """判断某模型是否已随包分发/已下载到用户目录（不含开发机共享回退）。

    仅看随包目录 <size>/model.bin 是否存在，用于「听写·模型」下拉框的
    已安装/未安装标记与默认选中。
    """
    for d in local_model_dirs(model_size):
        try:
            if d.is_dir() and (d / "model.bin").is_file():
                return True
        except OSError:
            continue
    return False


# 将 Hugging Face 模型缓存重定向到项目目录/用户目录。
# 注意：config 被 gui.main_window 在应用启动时导入，早于任何
# faster_whisper / huggingface_hub 的 import，因此此环境变量必然先生效。
_HF_HOME = PROJECT_ROOT / "models" / "hf_cache"
if getattr(sys, "frozen", False):
    _HF_HOME = user_data_dir() / "models" / "hf_cache"
os.environ.setdefault("HF_HOME", str(_HF_HOME))


def setup_whisper_env():
    """确保 Whisper 模型缓存位于 D 盘/用户目录（须在导入 faster_whisper 前调用）。"""
    os.environ.setdefault("HF_HOME", str(_HF_HOME))


def detect_gpu() -> bool:
    """检测是否有可用的 NVIDIA CUDA GPU（以 ctranslate2 视角判断）"""
    try:
        import ctranslate2
    except Exception:
        return False
    try:
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def resolve_whisper_model(model_size: str) -> str | None:
    """解析本地 Whisper 模型目录。优先级：
      1) 应用内 models/whisper/<size>（随 dist 分发，即开即用）
      2) [冻结态] 用户可写目录 %APPDATA%\\Transallum\\models\\whisper\\<size>（联网补充）
      3) 环境变量 TRANSALLUM_SHARED_MODELS 指定的共享目录（可选）
    返回模型目录路径；本地不存在返回 None。"""
    candidates = local_model_dirs(model_size)
    if _SHARED_MODELS_DIR is not None:
        candidates.append(_SHARED_MODELS_DIR / model_size)
    for d in candidates:
        try:
            if d.is_dir() and (d / "model.bin").is_file():
                return str(d)
        except OSError:
            continue
    return None


# ── 支持的格式定义 ──
MEDIA_FORMATS = {
    "video": {
        "input":  [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".mpg", ".mpeg"],
        "output": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".gif"],
        "label": "视频"
    },
    "audio": {
        "input":  [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus", ".aiff", ".alac"],
        "output": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"],
        "label": "音频"
    }
}

DOC_FORMATS = {
    "input":  [".pdf"],
    "output": [".docx", ".txt"],
    "label": "文档"
}

OCR_FORMATS = {
    "input":  [".pdf"],
    "output": [".txt", ".docx"],
    "label": "OCR"
}

TRANSCRIBE_FORMATS = {
    "input":  [".mp3", ".wav", ".mp4", ".avi", ".mkv", ".mov", ".flv", ".webm",
                ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"],
    "output": [".txt", ".srt", ".vtt"],
    "label": "听写"
}

# ── 格式 → FFmpeg 编码参数映射 ──
# 每组参数保证最佳质量/兼容性
FFMPEG_ENCODE_ARGS = {
    # 视频格式
    ".mp4":  ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k"],
    ".avi":  ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k"],
    ".mkv":  ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k"],
    ".mov":  ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k"],
    ".wmv":  ["-c:v", "wmv2", "-c:a", "wmav2", "-b:a", "192k"],
    ".flv":  ["-c:v", "flv", "-c:a", "aac", "-b:a", "192k"],
    ".webm": ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-c:a", "libopus"],
    ".gif":  ["-vf", "fps=10,scale=480:-1:flags=lanczos", "-loop", "0"],
    # 音频格式
    ".mp3":  ["-c:a", "libmp3lame", "-b:a", "320k"],
    ".wav":  ["-c:a", "pcm_s16le"],
    ".flac": ["-c:a", "flac", "-compression_level", "8"],
    ".aac":  ["-c:a", "aac", "-b:a", "256k"],
    ".ogg":  ["-c:a", "libvorbis", "-q:a", "6"],
    ".wma":  ["-c:a", "wmav2", "-b:a", "192k"],
    ".m4a":  ["-c:a", "aac", "-b:a", "256k"],
    ".opus": ["-c:a", "libopus", "-b:a", "128k"],
}


def parse_time(text: str) -> float | None:
    """解析时间字符串为秒。支持：纯秒 "98"、分:秒 "1:38"、时:分:秒 "0:01:38"。
    空串 / 非法 / 负数返回 None。"""
    text = (text or "").strip()
    if not text:
        return None
    try:
        parts = text.split(":")
        if len(parts) == 1:
            sec = float(parts[0])
        elif len(parts) == 2:
            sec = int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        else:
            return None
        return sec if sec >= 0 else None
    except (ValueError, TypeError):
        return None


def get_encode_args(output_fmt: str, input_fmt: str | None = None) -> list:
    """获取与目标格式匹配的 FFmpeg 编码参数"""
    ext = output_fmt.lower() if output_fmt.startswith(".") else f".{output_fmt.lower()}"
    args = FFMPEG_ENCODE_ARGS.get(ext)
    if args:
        return list(args)
    # 默认：copy 编码（快速但可能不兼容）
    return ["-c", "copy"]


def _local_tool_path(name: str) -> str | None:
    """在项目 tools/ 目录下查找可执行文件"""
    if not TOOLS_DIR.exists():
        return None
    exe_name = name + (".exe" if sys.platform == "win32" else "")
    # 优先按已知结构查找
    known_dirs = {
        "ffmpeg":    [TOOLS_DIR / "ffmpeg" / "bin"],
        "ffprobe":   [TOOLS_DIR / "ffmpeg" / "bin"],
        "tesseract": [TOOLS_DIR / "tesseract"],
    }
    for d in known_dirs.get(name, []):
        candidate = d / exe_name
        if candidate.is_file():
            return str(candidate)
    # 递归搜索整个 tools/
    for root, _, files in os.walk(str(TOOLS_DIR)):
        if exe_name in files:
            return os.path.join(root, exe_name)
    return None


def find_exe(name: str) -> str | None:
    """查找可执行文件：优先项目本地 > 系统 PATH > 官方安装器默认路径"""
    # 1) 项目本地 tools/
    local = _local_tool_path(name)
    if local:
        return local
    # 2) 系统 PATH
    exe = shutil.which(name)
    if exe:
        return exe
    # 3) 官方安装器的默认安装位置
    if sys.platform == "win32":
        fallback = {
            "tesseract": [r"C:\Program Files\Tesseract-OCR\tesseract.exe"],
        }
        for path in fallback.get(name, []):
            if os.path.isfile(path):
                return path
    return None


def check_tool(name: str) -> dict:
    """检测工具是否可用"""
    exe = find_exe(name)
    if exe:
        try:
            result = subprocess.run(
                [exe, "--version"], capture_output=True, text=True, timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else result.stderr.split("\n")[0]
            return {"available": True, "path": exe, "version": version_line}
        except Exception:
            return {"available": True, "path": exe, "version": "未知"}
    return {"available": False, "path": None, "version": None}


def check_all_tools() -> dict:
    """检测所有外部工具"""
    return {
        "ffmpeg": check_tool("ffmpeg"),
        "tesseract": check_tool("tesseract"),
    }


WHISPER_MODELS = {
    "tiny":       {"size_mb": 75,   "vram_gb": 1, "speed": "最快", "accuracy": "一般"},
    "tiny.en":    {"size_mb": 75,   "vram_gb": 1, "speed": "最快", "accuracy": "一般（仅英文）"},
    "base":       {"size_mb": 145,  "vram_gb": 1, "speed": "快",   "accuracy": "较好"},
    "base.en":    {"size_mb": 145,  "vram_gb": 1, "speed": "快",   "accuracy": "较好（仅英文）"},
    "small":      {"size_mb": 488,  "vram_gb": 2, "speed": "中等", "accuracy": "好"},
    "small.en":   {"size_mb": 488,  "vram_gb": 2, "speed": "中等", "accuracy": "好（仅英文）"},
    "medium":     {"size_mb": 1530, "vram_gb": 5, "speed": "慢",   "accuracy": "很好"},
    "medium.en":  {"size_mb": 1530, "vram_gb": 5, "speed": "慢",   "accuracy": "很好（仅英文）"},
    "large-v3":   {"size_mb": 3100, "vram_gb": 10,"speed": "最慢", "accuracy": "最佳"},
}
