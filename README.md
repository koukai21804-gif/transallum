# ◈ Transallum — 万能转换器

Windows 桌面万能格式转换工具，基于 **PyQt6 + PyInstaller(onedir)**。

![功能] 音视频互转 · PDF→文档 · OCR 识别 · AI 听写（faster-whisper，支持 CPU/GPU）

---

## ✨ 功能特性

| 模块 | 说明 |
|---|---|
| 🎬 **音视频互转** | FFmpeg 内核，支持 mp4/avi/mkv/mov/webm/... 互转，mp4→mp3 等；支持**截取片段**（如 24s~98s） |
| 📄 **PDF → 文档** | PDF → Word(.docx) / 纯文本(.txt)，基于 PyMuPDF / pdfplumber |
| 🔍 **OCR 识别** | 图片型 PDF → 文字，基于 Tesseract（中/英/日/韩等多语言） |
| 🎙 **AI 听写** | 音视频 → 文字(.txt/.srt/.vtt)，基于 faster-whisper，自动检测 GPU（CUDA）加速 |
| 🌗 **主题 / 🌐 双语** | 深色/浅色主题切换，中英界面实时切换 |

## 🖥 环境要求

- Windows 10/11（64 位）
- Python **3.12**（本项目使用 3.12.10）
- NVIDIA 显卡 + CUDA 驱动（可选，GPU 加速仅转录需要）

## 🔧 安装与运行（开发模式）

```bash
# 1. 创建虚拟环境（务必放在 D 盘，勿装 C 盘）
python -m venv D:\CC_project\transallum\venv

# 2. 安装依赖
D:\CC_project\transallum\venv\Scripts\pip install -r requirements.txt

# 3. 放置外部工具（目录结构见下）

# 4. 启动
D:\CC_project\transallum\venv\Scripts\python main.py
```

### 外部工具目录（`tools/`，已 gitignore）

```
tools/
├── ffmpeg/
│   └── bin/
│       ├── ffmpeg.exe
│       └── ffprobe.exe
└── tesseract/
    ├── tesseract.exe
    └── tessdata/   # chi_sim.traineddata 等语言包
```

程序按 **项目 tools/ → 系统 PATH → 常见安装路径** 顺序查找工具。

### Whisper 模型（`models/whisper/`）

转录所需的 faster-whisper 模型放在：

```
models/whisper/
├── tiny/       # ~75MB
└── large-v3/   # ~3GB（可选项）
```

每个模型目录需含 `model.bin`（ctranslate2 格式）。打包后的程序会优先读取应用内
`models/whisper/`，缺失时回退到开发机共享目录。模型缓存（HF_HOME）也已重定向到
`models/hf_cache/`，全部位于 D 盘。

## 📦 打包（PyInstaller onedir）

```bash
# 1. 清理旧产物（如正在运行请先结束进程）
taskkill /F /IM Transallum.exe
rm -rf build dist/Transallum

# 2. 打包
venv\Scripts\pyinstaller transallum.spec --noconfirm

# 3. 补充外部工具与模型（spec 不内置这些大文件）
mkdir -p dist/Transallum/tools dist/Transallum/models
cp -r tools/ffmpeg        dist/Transallum/tools/
cp -r tools/tesseract     dist/Transallum/tools/
cp -r models/whisper      dist/Transallum/models/whisper   # 或使用 junction 去重（见下）

# 4. 运行
dist\Transallum\Transallum.exe
```

### 模型去重（junction，可选）

若不想在 `dist/` 内复制 3GB 模型，可建立目录链接（Windows junction，无需管理员）：

```cmd
mklink /J dist\Transallum\models\whisper  D:\CC_project\transallum\models\whisper
```

### 打包后 GPU 自检

```cmd
dist\Transallum\Transallum.exe --selftest-gpu
```

日志写入 `logs\selftest.log`，逐步输出导入 faster-whisper / 检测 GPU / 加载模型 / 试转写
的进度，用于远程排障。

## 🗂 项目结构

```
transallum/
├── main.py                # 入口（含 --selftest-gpu 自检）
├── transallum.spec        # PyInstaller 打包配置（onedir + CUDA DLL 归位）
├── runtime_hook.py        # 运行时 hook：禁止子进程弹出 CMD 窗口
├── requirements.txt       # 依赖清单
├── ruff.toml              # ruff 静态检查配置
├── gui/
│   ├── main_window.py     # 主窗口（4 个功能页）
│   └── workers.py         # QThread 工作线程（媒体转换 / OCR / 转录）
├── utils/
│   ├── config.py          # 工具检测、格式映射、GPU/模型解析
│   ├── i18n.py            # 中英双语
│   └── themes.py          # 深浅主题
└── scripts/
    └── download_whisper_model.py  # 模型下载脚本
```

## 🔍 静态检查

```bash
venv\Scripts\python -m ruff check main.py gui utils scripts
```

`ruff.toml` 中显式放行了三类**刻意**的规则（见文件内注释）：
盲捕获异常（worker 线程保证 GUI 不崩溃）、静默容错的清理路径、
手动检查 returncode 的 subprocess 调用。

## 🛠 常见问题

| 问题 | 原因 / 解决 |
|---|---|
| 转换报 "源文件不包含音频流" | 源是静音录屏或纯视频，本身无音轨，无法转 mp3 |
| 转换后文件只有 1 秒 / 覆盖了原文件 | 输出格式与源相同导致输出路径=输入路径，已内置「防覆盖」守卫并自动切换格式 |
| 打包版切 GPU 反复弹窗/报错 | CUDA DLL 未随包分发或子进程弹 CMD 窗口；已通过 onedir 布局 + runtime_hook 修复，用 `--selftest-gpu` 验证 |
| 首次转录很慢 | 模型首次需加载/下载，属于正常现象 |

## 📜 协议

仅供个人学习使用。
