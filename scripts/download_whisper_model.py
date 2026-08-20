"""预下载 faster-whisper 模型（从魔搭镜像获取，无需访问 Hugging Face）

用法:
    python scripts/download_whisper_model.py              # 下载全部可选模型
    python scripts/download_whisper_model.py large-v3     # 下载指定模型
    python scripts/download_whisper_model.py large-v3 small

说明:
    - 模型保存在 项目目录/models/whisper/<size>/ 下（D 盘，不占 C 盘）
    - Transallum 转换时会优先使用本地模型，无需联网
"""
import shutil
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "whisper"

# 魔搭镜像可用模型（多语言版）。
# 注：tiny.en/base.en/small.en/medium.en 英文专属版在魔搭无镜像，
# 请改用对应的多语言版（对英文同样支持良好）。
AVAILABLE = {
    "tiny":      "faster-whisper-tiny",
    "base":      "faster-whisper-base",
    "small":     "faster-whisper-small",
    "medium":    "faster-whisper-medium",
    "large-v3":  "faster-whisper-large-v3",
}

# 必需文件 + 可选文件（vocabulary 可能是 .json 或 .txt，取决于模型）
REQUIRED_FILES = ["config.json", "model.bin", "tokenizer.json"]
OPTIONAL_FILES = ["preprocessor_config.json", "vocabulary.json", "vocabulary.txt"]

BASE_URL = ("https://modelscope.cn/models/{repo}/resolve/master/{file}")


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Transallum/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def file_exists(url: str) -> bool:
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "Transallum/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 200
    except Exception:
        return False


def download_file(url: str, dest: Path, resume: bool = True) -> bool:
    """下载单个文件，支持断点续传（大文件中断后可从断点继续）"""
    headers = {"User-Agent": "Transallum/1.0"}
    mode = "wb"
    if resume and dest.exists() and dest.stat().st_size > 0:
        headers["Range"] = f"bytes={dest.stat().st_size}-"
        mode = "ab"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, mode) as out:
            shutil.copyfileobj(resp, out, length=1 << 20)
        return True
    except Exception as e:
        print(f"  [失败] {dest.name}: {e}")
        return False


def download_model(size: str) -> bool:
    if size not in AVAILABLE:
        print(f"  [跳过] 模型 '{size}' 不在魔搭镜像列表中。可用: "
              + ", ".join(AVAILABLE))
        print("  （.en 英文专属版请改用对应的多语言版）")
        return False

    repo = AVAILABLE[size]
    target = MODELS_DIR / size
    target.mkdir(parents=True, exist_ok=True)
    print(f"── 下载 {size}  →  {target}")

    ok = True
    # 必需文件
    for f in REQUIRED_FILES:
        url = BASE_URL.format(repo=repo, file=f)
        print(f"  [下载] {f} ...")
        ok = download_file(url, target / f) and ok

    # 可选文件：vocabulary 优先 .json，缺失则回退 .txt
    vocab_done = False
    for f in ["vocabulary.json", "vocabulary.txt"]:
        url = BASE_URL.format(repo=repo, file=f)
        if file_exists(url):
            print(f"  [下载] {f} ...")
            ok = download_file(url, target / f) and ok
            vocab_done = True
            break
    if not vocab_done:
        print("  [提示] 仓库无 vocabulary 文件（部分新模型已合并进 tokenizer）")

    # 其他可选文件
    for f in OPTIONAL_FILES:
        if f in ("vocabulary.json", "vocabulary.txt"):
            continue
        url = BASE_URL.format(repo=repo, file=f)
        if file_exists(url):
            print(f"  [下载] {f} ...")
            ok = download_file(url, target / f) and ok

    # 校验 model.bin 完整
    mb = target / "model.bin"
    if mb.exists() and mb.stat().st_size > 0:
        print(f"  [完成] {size}: model.bin = {mb.stat().st_size:,} bytes")
    else:
        print(f"  [失败] {size}: model.bin 缺失或为 0 字节")
        ok = False
    return ok


def main():
    args = sys.argv[1:]
    sizes = [a for a in args if not a.startswith("-")] or list(AVAILABLE)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"模型保存目录: {MODELS_DIR}")
    all_ok = True
    for size in sizes:
        all_ok = download_model(size) and all_ok
    print("=" * 48)
    print("全部完成 ✅" if all_ok else "部分模型下载失败，请检查网络后重试")


if __name__ == "__main__":
    main()
