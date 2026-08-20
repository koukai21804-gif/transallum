# -*- mode: python ; coding: utf-8 -*-
"""Transallum PyInstaller spec — onedir 模式，外挂 FFmpeg + Tesseract"""

import os
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH)  # spec 文件所在目录 = 项目根

# faster-whisper 的内置资源（VAD 模型 silero_vad_v6.onnx 等）必须随包分发
# 否则打包后 vad_filter=True 会报 ONNXRuntimeError: NO_SUCHFILE
import faster_whisper
_FW_ASSETS = os.path.join(os.path.dirname(os.path.abspath(faster_whisper.__file__)), "assets")

# CUDA 运行时库（GPU 加速必需）。ctranslate2 在运行时动态加载这些 DLL，
# PyInstaller 不会自动收集，必须显式打入并与 ctranslate2.dll 同目录。
import ctranslate2
_CT2_DIR = os.path.dirname(os.path.abspath(ctranslate2.__file__))
_CUDA_DLLS = ["cublas64_12.dll", "cublasLt64_12.dll", "cudart64_12.dll", "cudnn64_9.dll"]
_CUDA_BINARIES = [
    (os.path.join(_CT2_DIR, dll), 'ctranslate2')
    for dll in _CUDA_DLLS if os.path.isfile(os.path.join(_CT2_DIR, dll))
]

a = Analysis(
    ['main.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=_CUDA_BINARIES,
    datas=[
        (_FW_ASSETS, 'faster_whisper/assets'),
    ],
    hiddenimports=[
        # GUI
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
        # 文档转换
        'pdfplumber', 'pdfminer', 'fitz',    # PyMuPDF
        'docx', 'lxml',
        # OCR
        'pytesseract', 'PIL',
        # AI 听写
        'faster_whisper', 'ctranslate2',
        'av', 'onnxruntime',
        'huggingface_hub', 'tokenizers',
        'tqdm', 'httpx', 'httpcore', 'anyio',
        'h11', 'certifi', 'idna',
        # 工具
        'subprocess', 'tempfile', 'shutil', 'pathlib',
        # faster-whisper 子模块
        'faster_whisper.transcribe', 'faster_whisper.audio',
        'faster_whisper.vad', 'faster_whisper.tokenizer',
        'faster_whisper.utils',
        # ctranslate2 子模块
        'ctranslate2.converters', 'ctranslate2.models',
        'ctranslate2.specs',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(PROJECT_ROOT / 'runtime_hook.py')],
    excludes=['torch', 'torchvision', 'easyocr', 'scipy', 'sympy',
              'matplotlib', 'numpy.random', 'pandas', 'cv2'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# 标准 onedir：exe 只含 bootloader+pyz+脚本，所有 binaries/datas 进 _internal/。
# 这样 ~800MB 的 CUDA DLL 不必在每次启动时解压到 C 盘 %TEMP%\_MEIxxxxx，
# 既避免解压失败导致的原生崩溃，也符合"依赖只放 D 盘"的要求。
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Transallum',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'gui' / 'icon.ico') if (PROJECT_ROOT / 'gui' / 'icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Transallum',
)
