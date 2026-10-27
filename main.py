"""Transallum — 万能转换器 入口"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow
from utils.config import user_data_dir
from utils.themes import DARK, build_stylesheet

# 冻结态（安装版）写到 %APPDATA%\\Transallum\\logs\\，开发态 PROJECT_ROOT\\logs\\。
# 安装到 Program Files（只读）后靠此重定向避免写权限崩溃。
_SELF_TEST_LOG = str(user_data_dir() / "logs" / "selftest.log")


def _selftest_gpu():
    """打包后 GPU 自检：在真实运行环境中逐步加载 CUDA/模型并写日志。
    用于远程排障——每步写完即落盘，即使中途原生崩溃也能看出卡在哪一步。"""
    import time

    def rec(msg):
        try:
            os.makedirs(os.path.dirname(_SELF_TEST_LOG), exist_ok=True)
            with open(_SELF_TEST_LOG, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    t0 = time.time()
    rec(f"===== GPU 自检开始 (pid={os.getpid()}) =====")
    try:
        rec("步骤1: 导入 faster_whisper（加载 ctranslate2）")
        from faster_whisper import WhisperModel
        rec("步骤1 完成")
    except Exception as e:
        rec(f"步骤1 失败: {type(e).__name__}: {e}")
        return 1

    try:
        rec("步骤2: detect_gpu()")
        from utils.config import detect_gpu, resolve_whisper_model
        gpu_ok = detect_gpu()
        rec(f"步骤2 完成: gpu_ok={gpu_ok}")
    except Exception as e:
        rec(f"步骤2 失败: {type(e).__name__}: {e}")
        return 1

    if not gpu_ok:
        rec("GPU 不可用——预期是找到 GPU，请检查驱动/CUDA DLL")
        return 1

    try:
        rec("步骤3: 解析本地模型 large-v3")
        local = resolve_whisper_model("large-v3")
        rec(f"步骤3 完成: local_model={local}")
        if not local:
            rec("large-v3 模型未找到（安装包只需打包 large-v3）")
            return 1
    except Exception as e:
        rec(f"步骤3 失败: {type(e).__name__}: {e}")
        return 1

    try:
        rec("步骤4: WhisperModel(cuda, float16) 加载")
        model = WhisperModel(local, device="cuda", compute_type="float16",
                             local_files_only=True)
        rec("步骤4 完成: 模型加载成功")
    except Exception as e:
        import traceback
        rec(f"步骤4 失败: {type(e).__name__}: {e}")
        rec(traceback.format_exc())
        return 1

    try:
        rec("步骤5: 简单转录 2 秒静音验证")
        import numpy as np
        audio = np.zeros(16000 * 2, dtype=np.float32)
        segs, _ = model.transcribe(audio, beam_size=1)
        count = sum(1 for _ in segs)
        rec(f"步骤5 完成: 转录成功, segments={count}")
    except Exception as e:
        import traceback
        rec(f"步骤5 失败: {type(e).__name__}: {e}")
        rec(traceback.format_exc())
        return 1

    rec(f"===== GPU 自检通过，总耗时 {time.time()-t0:.1f}s =====")
    return 0


def _verify():
    """免 GPU 的安装完整性自检：large-v3 模型就位、无多余模型、工具齐全。

    返回退出码：0=通过，1=有问题。用于安装工具的静默验证（无需显卡）。
    """
    from utils.config import WHISPER_MODELS_DIR, find_exe, resolve_whisper_model
    problems = []
    model = resolve_whisper_model("large-v3")
    if not model:
        problems.append("large-v3 模型缺失")
    if (WHISPER_MODELS_DIR / "tiny").exists():
        problems.append("检测到未随包提供的 tiny 模型")
    for tool in ("ffmpeg", "ffprobe", "tesseract"):
        if not find_exe(tool):
            problems.append(f"{tool} 工具缺失")
    if problems:
        print("verify 检查失败:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("verify 通过: large-v3/工具就位, 无多余模型")
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest-gpu":
        sys.exit(_selftest_gpu())
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        sys.exit(_verify())
    app = QApplication(sys.argv)
    app.setApplicationName("Transallum")

    # 初始加载深色主题
    app.setStyleSheet(build_stylesheet(DARK))

    font = QFont(DARK["font_family"], 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
