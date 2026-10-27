# ◈ Transallum — Universal Converter

Windows desktop universal format converter, built on **PyQt6 + PyInstaller(onedir)**.

English | [简体中文](README.md)

Features: audio/video conversion · PDF → documents · OCR · AI transcription (faster-whisper, CPU/GPU)

---

## ✨ Features

| Module | Description |
|---|---|
| 🎬 **Audio/Video** | FFmpeg-powered conversion between mp4/avi/mkv/mov/webm/..., mp4→mp3, etc.; supports **clip trimming** (e.g. 24s~98s) |
| 📄 **PDF → Document** | PDF → Word(.docx) / plain text(.txt), via PyMuPDF / pdfplumber |
| 🔍 **OCR** | Image-based PDF → text, via Tesseract (Chinese/English/Japanese/Korean and more) |
| 🎙 **AI Transcription** | Audio/video → text(.txt/.srt/.vtt), via faster-whisper with automatic GPU (CUDA) detection |
| 🌗 **Theming** | Dark/light themes plus **custom themes**: 26 independently adjustable color slots, background images & opacity for window/sidebar — dark and light schemes are stored separately |
| 🌐 **Bilingual UI** | Live switching between Chinese and English |

## 🖥 Requirements

- Windows 10/11 (64-bit)
- Python **3.12**
- NVIDIA GPU + CUDA driver (optional — GPU acceleration only affects transcription)

## 🔧 Install & Run (development mode)

```bash
git clone https://github.com/koukai21804-gif/transallum.git
cd transallum

# 1. Create a virtual environment
python -m venv venv

# 2. Install dependencies
venv\Scripts\pip install -r requirements.txt
venv\Scripts\pip install -r requirements-dev.txt   # dev/test only (pytest)

# 3. Place external tools (see below)

# 4. Start
venv\Scripts\python main.py
```

### External tools directory (`tools/`, gitignored)

```
tools/
├── ffmpeg/
│   └── bin/
│       ├── ffmpeg.exe
│       └── ffprobe.exe
└── tesseract/
    ├── tesseract.exe
    └── tessdata/   # chi_sim.traineddata and other language packs
```

Where to get them:

- **FFmpeg**: [gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/) (release-full package) or
  [BtbN builds](https://github.com/BtbN/FFmpeg-Builds/releases) — copy `ffmpeg.exe` and
  `ffprobe.exe` from `bin/` into `tools/ffmpeg/bin/`
- **Tesseract**: the [UB Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki)
  (lets you tick Chinese language packs) — copy the installation into `tools/tesseract/`,
  or let the app discover a default installation automatically

Tools are looked up in this order: **project `tools/` → system PATH → official installer
default locations**. If nothing is found, the affected feature page says so.

### Whisper models (`models/whisper/`)

faster-whisper models used for transcription live in:

```
models/whisper/
├── tiny/       # ~75MB, for quick testing
└── large-v3/   # ~3GB, best accuracy
```

Recommended: download via the script (ModelScope mirror, no Hugging Face access needed):

```bash
venv\Scripts\python scripts\download_whisper_model.py            # all available models
venv\Scripts\python scripts\download_whisper_model.py large-v3   # a single model
```

Or place them manually: each model directory must contain `model.bin` (ctranslate2 format,
available from the Hugging Face `Systran/faster-whisper-*` repos).

Model resolution order: **bundled `models/whisper/<size>` → [installed build] user directory
`%APPDATA%\Transallum\models\whisper\<size>` → the shared directory pointed to by the
`TRANSALLUM_SHARED_MODELS` environment variable**. Multiple working copies can share one
big model: set the variable to a shared `models/whisper` directory. The model cache
(HF_HOME) is redirected to `models/hf_cache/` (user data directory for the installed
build), keeping the C drive clean.

## 🧪 Tests & Static Checks

```bash
venv\Scripts\python -m pytest tests
venv\Scripts\python -m ruff check main.py gui utils scripts
```

`ruff.toml` explicitly allows three categories of **intentional** rules (see comments in the
file): blind exception catching (worker threads keep the GUI alive), silently tolerant
cleanup paths, and subprocess calls whose returncode is checked manually.

## 📦 Packaging (PyInstaller onedir)

```bash
# 1. Clean old artifacts (kill the app first if it is running)
taskkill /F /IM Transallum.exe
rm -rf build dist/Transallum

# 2. Build
venv\Scripts\pyinstaller transallum.spec --noconfirm

# 3. Add external tools and models (the spec does not bundle these big files)
mkdir -p dist/Transallum/tools dist/Transallum/models
cp -r tools/ffmpeg        dist/Transallum/tools/
cp -r tools/tesseract     dist/Transallum/tools/
cp -r models/whisper      dist/Transallum/models/whisper   # or dedupe with a junction (below)

# 4. Run
dist\Transallum\Transallum.exe
```

### Model deduplication (junction, optional)

To avoid copying the 3GB model into `dist/`, create a directory link (Windows junction,
no admin needed):

```cmd
mklink /J dist\Transallum\models\whisper D:\path\to\transallum\models\whisper
```

### Post-build self checks

```cmd
dist\Transallum\Transallum.exe --selftest-gpu   # GPU acceleration path (needs a GPU)
dist\Transallum\Transallum.exe --verify          # GPU-free install integrity check (for silent installer runs)
```

`--selftest-gpu` writes to `%APPDATA%\Transallum\logs\selftest.log`, logging each step —
importing faster-whisper / detecting the GPU / loading the model / a trial transcription —
for remote troubleshooting.

## 🗂 Project Structure

```
transallum/
├── main.py                       # Entry point (--selftest-gpu / --verify self checks)
├── transallum.spec               # PyInstaller config (onedir + CUDA DLL placement)
├── runtime_hook.py               # Runtime hook: no CMD windows from subprocesses
├── requirements.txt              # Dependency list
├── requirements-dev.txt          # Dev dependencies (pytest)
├── ruff.toml                     # ruff linter config
├── gui/
│   ├── main_window.py            # Main window (4 feature pages)
│   ├── workers.py                # QThread workers (media conversion / OCR / transcription)
│   ├── background.py             # Window/sidebar background layer (cover scaling + opacity)
│   └── theme_settings_dialog.py  # Custom theme settings dialog
├── utils/
│   ├── config.py                 # Tool detection, format maps, GPU/model resolution, path redirection
│   ├── i18n.py                   # Chinese/English strings
│   ├── themes.py                 # Dark/light palettes + QSS generation
│   ├── theme_settings.py         # Custom theme persistence (per theme, with legacy migration)
│   └── color_utils.py            # Color parsing (#RRGGBB / rgba)
├── tests/                        # pytest suite
└── scripts/
    └── download_whisper_model.py # Model download script (ModelScope mirror)
```

## 🛠 FAQ

| Problem | Cause / Fix |
|---|---|
| "The source has no audio stream" | The source is a muted screen recording or a video-only file; mp3 extraction is impossible without an audio track |
| Output is 1 second long / overwrote the source | Same input and output format made the paths collide; an overwrite guard is built in and the format is switched automatically |
| Installed build keeps popping up errors on GPU switch | CUDA DLLs were not shipped or subprocesses flashed CMD windows; fixed via the onedir layout + runtime hook — verify with `--selftest-gpu` |
| First transcription is slow | The model loads/downloads on first use; this is normal |

## 📜 License

[MIT License](LICENSE)
