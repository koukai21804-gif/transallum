"""PyInstaller runtime hook — 窗口程序禁止所有子进程弹出 CMD 窗口。

打包为 console=False 的窗口程序后，任何不带 CREATE_NO_WINDOW 的子进程
（ffmpeg/ffprobe/tesseract/pandoc 等控制台程序）都会闪一个命令提示符窗口。
本 hook 在解释器初始化时全局给 subprocess.Popen 打补丁：未显式指定
creationflags 时默认加 CREATE_NO_WINDOW，一次性覆盖全应用（含 pytesseract 内部调用）。
"""
import subprocess

if hasattr(subprocess, "CREATE_NO_WINDOW"):
    _Popen_init = subprocess.Popen.__init__

    def _popen_init_no_window(self, *args, **kwargs):
        if kwargs.get("creationflags") is None:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        _Popen_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = _popen_init_no_window
