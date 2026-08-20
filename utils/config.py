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

# ── Whisper 模型本地目录（全部放 D 盘，不占 C 盘） ──
WHISPER_MODELS_DIR = PROJECT_ROOT / "models" / "whisper"
# 兼容路径：打包后 dist 内未带模型时，回退到开发机共享模型目录
_SHARED_MODELS_DIR = Path(r"D:\CC_project\transallum\models\whisper")

# 将 Hugging Face 模型缓存重定向到 D 盘。
# 注意：config 被 gui.main_window 在应用启动时导入，早于任何
# faster_whisper / huggingface_hub 的 import，因此此环境变量必然先生效。
os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / "models" / "hf_cache"))


def setup_whisper_env():
    """确保 Whisper 模型缓存位于 D 盘（须在导入 faster_whisper 前调用）。"""
    os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / "models" / "hf_cache"))


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
      2) 开发机共享目录 D:\\CC_project\\transallum\\models\\whisper\\<size>
    返回模型目录路径；本地不存在返回 None。"""
    candidates = [
        WHISPER_MODELS_DIR / model_size,
        _SHARED_MODELS_DIR / model_size,
    ]
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
    """查找可执行文件：优先项目本地 > 系统 PATH > 常见安装路径"""
    # 1) 项目本地 tools/
    local = _local_tool_path(name)
    if local:
        return local
    # 2) 系统 PATH
    exe = shutil.which(name)
    if exe:
        return exe
    # 3) Windows 常见路径（向后兼容）
    if sys.platform == "win32":
        fallback = {
            "ffmpeg": [
                r"D:\ffmpeg\bin\ffmpeg.exe",
                r"D:\tools\ffmpeg\bin\ffmpeg.exe",
            ],
            "tesseract": [
                r"D:\Tesseract-OCR\tesseract.exe",
            ],
            "pandoc": [
                r"D:\Pandoc\pandoc.exe",
            ],
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
