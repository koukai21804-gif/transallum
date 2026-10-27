# ◈ Transallum — 万能转换器

Windows 桌面万能格式转换工具，基于 **PyQt6 + PyInstaller(onedir)**。

English | [简体中文](#-transallum--万能转换器) · [README in English](README_EN.md)

![功能] 音视频互转 · PDF→文档 · OCR 识别 · AI 听写（faster-whisper，支持 CPU/GPU）

---

## ✨ 功能特性

| 模块 | 说明 |
|---|---|
| 🎬 **音视频互转** | FFmpeg 内核，支持 mp4/avi/mkv/mov/webm/... 互转，mp4→mp3 等；支持**截取片段**（如 24s~98s） |
| 📄 **PDF → 文档** | PDF → Word(.docx) / 纯文本(.txt)，基于 PyMuPDF / pdfplumber |
| 🔍 **OCR 识别** | 图片型 PDF → 文字，基于 Tesseract（中/英/日/韩等多语言） |
| 🎙 **AI 听写** | 音视频 → 文字(.txt/.srt/.vtt)，基于 faster-whisper，自动检测 GPU（CUDA）加速 |
| 🌗 **主题** | 深色/浅色切换，支持**自定义主题**：26 个颜色槽独立调色 + 窗口/导航栏背景图与透明度，深浅两套方案互不共享 |
| 🌐 **双语** | 中英界面实时切换 |

## 🖥 环境要求

- Windows 10/11（64 位）
- Python **3.12**
- NVIDIA 显卡 + CUDA 驱动（可选，GPU 加速仅转录需要）

## 🔧 安装与运行（开发模式）

```bash
git clone https://github.com/koukai21804-gif/transallum.git
cd transallum

# 1. 创建虚拟环境
python -m venv venv

# 2. 安装依赖
venv\Scripts\pip install -r requirements.txt
venv\Scripts\pip install -r requirements-dev.txt   # 仅开发/测试需要（pytest）

# 3. 放置外部工具（目录结构见下）

# 4. 启动
venv\Scripts\python main.py
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

下载来源（任选其一）：

- **FFmpeg**：[gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/)（release-full 压缩包）或
  [BtbN builds](https://github.com/BtbN/FFmpeg-Builds/releases)，把 `bin/` 下的
  `ffmpeg.exe`、`ffprobe.exe` 拷入 `tools/ffmpeg/bin/`
- **Tesseract**：[UB Mannheim 安装器](https://github.com/UB-Mannheim/tesseract/wiki)（安装时可勾选中文语言包），
  整体拷入 `tools/tesseract/`，或安装后由程序自动从默认路径发现

程序按 **项目 tools/ → 系统 PATH → 官方安装器默认路径** 顺序查找工具，全部跳过时相关功能页会提示缺失。

### Whisper 模型（`models/whisper/`）

转录所需的 faster-whisper 模型放在：

```
models/whisper/
├── tiny/       # ~75MB，开发调试用
└── large-v3/   # ~3GB，精度最佳
```

推荐用脚本从魔搭镜像下载（无需访问 Hugging Face）：

```bash
venv\Scripts\python scripts\download_whisper_model.py            # 下载全部可选模型
venv\Scripts\python scripts\download_whisper_model.py large-v3   # 仅指定模型
```

也可手动放置：每个模型目录需含 `model.bin`（ctranslate2 格式，可从
Hugging Face `Systran/faster-whisper-*` 仓库获取）。

模型解析优先级：**应用内 `models/whisper/<size>` → [安装版] 用户目录
`%APPDATA%\Transallum\models\whisper\<size>` → 环境变量
`TRANSALLUM_SHARED_MODELS` 指向的共享目录**。多个开发副本可共用一份大模型：
把该变量设为共享的 `models/whisper` 目录即可。模型缓存（HF_HOME）重定向到
`models/hf_cache/`（安装版在用户数据目录），不占用 C 盘。

## 🧪 测试与静态检查

```bash
venv\Scripts\python -m pytest tests
venv\Scripts\python -m ruff check main.py gui utils scripts
```

`ruff.toml` 中显式放行了三类**刻意**的规则（见文件内注释）：
盲捕获异常（worker 线程保证 GUI 不崩溃）、静默容错的清理路径、
手动检查 returncode 的 subprocess 调用。

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
mklink /J dist\Transallum\models\whisper D:\path\to\transallum\models\whisper
```

### 打包后自检

```cmd
dist\Transallum\Transallum.exe --selftest-gpu   # GPU 加速链路自检（需显卡）
dist\Transallum\Transallum.exe --verify          # 免 GPU 安装完整性校验（供安装器静默调用）
```

`--selftest-gpu` 日志写入 `%APPDATA%\Transallum\logs\selftest.log`，逐步输出导入
faster-whisper / 检测 GPU / 加载模型 / 试转写的进度，用于远程排障。

## 🗂 项目结构

```
transallum/
├── main.py                       # 入口（含 --selftest-gpu / --verify 自检）
├── transallum.spec               # PyInstaller 打包配置（onedir + CUDA DLL 归位）
├── runtime_hook.py               # 运行时 hook：禁止子进程弹出 CMD 窗口
├── requirements.txt              # 依赖清单
├── requirements-dev.txt          # 开发依赖（pytest）
├── ruff.toml                     # ruff 静态检查配置
├── gui/
│   ├── main_window.py            # 主窗口（4 个功能页）
│   ├── workers.py                # QThread 工作线程（媒体转换 / OCR / 转录）
│   ├── background.py             # 窗口/导航栏背景层（cover 缩放 + 透明度）
│   └── theme_settings_dialog.py  # 自定义主题设置对话框
├── utils/
│   ├── config.py                 # 工具检测、格式映射、GPU/模型解析、路径重定向
│   ├── i18n.py                   # 中英双语
│   ├── themes.py                 # 深浅主题色板 + QSS 生成
│   ├── theme_settings.py         # 自定义主题持久化（按主题独立，含旧结构迁移）
│   └── color_utils.py            # 颜色解析（#RRGGBB / rgba）
├── tests/                        # pytest 测试套件
└── scripts/
    └── download_whisper_model.py # 模型下载脚本（魔搭镜像）
```

## 🛠 常见问题

| 问题 | 原因 / 解决 |
|---|---|
| 转换报 "源文件不包含音频流" | 源是静音录屏或纯视频，本身无音轨，无法转 mp3 |
| 转换后文件只有 1 秒 / 覆盖了原文件 | 输出格式与源相同导致输出路径=输入路径，已内置「防覆盖」守卫并自动切换格式 |
| 打包版切 GPU 反复弹窗/报错 | CUDA DLL 未随包分发或子进程弹 CMD 窗口；已通过 onedir 布局 + runtime_hook 修复，用 `--selftest-gpu` 验证 |
| 首次转录很慢 | 模型首次需加载/下载，属于正常现象 |

## 📜 协议

[MIT License](LICENSE)
