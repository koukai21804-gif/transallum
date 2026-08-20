"""后台工作线程 — 所有耗时操作通过 QThread 执行，不阻塞界面"""
import os
import subprocess
import traceback

from PyQt6.QtCore import QThread, pyqtSignal

from utils.i18n import t

# 诊断日志文件（固定在 D 盘，便于排查打包后的运行问题）
_DIAG_LOG = r"D:\CC_project\transallum\logs\worker.log"

# 窗口程序下禁止子进程弹出 CMD 窗口（打包后 console=False，必须显式设置）
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# 纯音频输出格式（只能容纳音频流，无法承载纯视频内容）
_AUDIO_ONLY_FORMATS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"}


def _norm_ext(fmt: str) -> str:
    """统一格式扩展名（补上前导点、小写）"""
    return fmt.lower() if fmt.startswith(".") else f".{fmt.lower()}"


def _same_path(a: str, b: str) -> bool:
    """判断两个路径是否指向同一文件（Windows 不区分大小写）。"""
    try:
        return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))
    except Exception:
        return False


def _friendly_ffmpeg_error(stderr: str) -> str | None:
    """将 FFmpeg 常见错误翻译成友好提示；无法识别时返回 None。"""
    s = stderr or ""
    if "does not contain any stream" in s:
        return t("error.no_stream")
    if "matches no streams" in s:
        return t("error.no_stream")
    return None


def _diag(msg: str):
    """追加诊断日志到 D 盘文件（不影响正常功能）"""
    try:
        os.makedirs(os.path.dirname(_DIAG_LOG), exist_ok=True)
        with open(_DIAG_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


class BaseWorker(QThread):
    """基础 Worker，提供统一的信号接口"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def cancel(self):
        self.requestInterruption()


# ─── 批量转换 Worker ─────────────────────────────────────────────

class BatchWorker(BaseWorker):
    """批量转换：顺序执行多个单文件转换任务"""
    file_progress = pyqtSignal(int)     # 当前文件进度 0-100
    file_index = pyqtSignal(int, int)   # 当前文件序号, 总文件数

    def __init__(self, tasks: list, parent=None):
        """
        tasks: [(input_path, output_path, WorkerClass, worker_kwargs), ...]
        """
        super().__init__(parent)
        self.tasks = tasks

    def run(self):
        total = len(self.tasks)
        success_count = 0
        failed = []

        for idx, (in_path, out_path, worker_cls, kwargs) in enumerate(self.tasks):
            if self.isInterruptionRequested():
                break

            self.file_index.emit(idx + 1, total)
            self.progress.emit(int(idx / total * 100))
            self.status.emit(f"[{idx + 1}/{total}] {os.path.basename(in_path)}")

            # 创建单文件 Worker 并同步等待
            worker = worker_cls(in_path, out_path, **kwargs)
            worker.progress.connect(lambda v: self.file_progress.emit(v))

            # 同步运行（在 QThread 内）
            worker.run()

            if worker.isInterruptionRequested():
                break

            # 检查结果（通过 finished 信号的最后一次 emit）
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                success_count += 1
                self.log.emit(f"  [OK] {os.path.basename(in_path)} → {os.path.basename(out_path)}")
            else:
                failed.append(os.path.basename(in_path))
                self.log.emit(f"  [FAIL] {os.path.basename(in_path)}")

        self.progress.emit(100)
        if failed:
            self.status.emit(f"完成: {success_count}/{total} 成功, {len(failed)} 失败")
            self.finished.emit(success_count > 0,
                               f"{success_count}/{total} 成功: {', '.join(failed[:3])}")
        else:
            self.status.emit(f"全部完成: {success_count}/{total}")
            self.finished.emit(True, f"{success_count}/{total} 个文件转换成功")


# ─── 音视频互转 Worker ───────────────────────────────────────────

class MediaConvertWorker(BaseWorker):
    """使用 FFmpeg 进行音视频格式转换"""

    def __init__(self, input_path: str, output_path: str,
                 output_format: str, parent=None,
                 start_time: float | None = None, end_time: float | None = None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.output_format = output_format
        self.start_time = start_time   # 截取起始秒（None = 不截取）
        self.end_time = end_time       # 截取结束秒（None = 不截取）

    def run(self):
        try:
            from utils.config import find_exe, get_encode_args

            ffmpeg = find_exe("ffmpeg") or "ffmpeg"
            ffprobe = find_exe("ffprobe") or "ffprobe"

            # 安全防护：禁止输出覆盖源文件（同路径/仅大小写不同均拦截）
            if _same_path(self.input_path, self.output_path):
                msg = t("error.same_file")
                self.log.emit(t("log.err") + " " + msg)
                self.finished.emit(False, msg)
                return

            self.status.emit(t("progress.ffmpeg_init"))
            self.progress.emit(0)

            # 纯音频输出 → 先确认源含音频流，否则给出明确提示（如静音录屏）
            if _norm_ext(self.output_format) in _AUDIO_ONLY_FORMATS \
                    and not self._has_audio_stream(ffprobe, self.input_path):
                self.log.emit(t("log.err") + " " + t("error.no_audio_stream"))
                self.finished.emit(False, t("error.no_audio_stream"))
                return

            # 获取目标格式编码参数
            encode_args = get_encode_args(self.output_format)

            duration_sec = self._get_duration(ffprobe, self.input_path)

            # 截取片段时，进度条以「截取时长」为准
            if duration_sec is not None and self.start_time is not None and self.end_time is not None:
                duration_sec = self.end_time - self.start_time

            if duration_sec is None:
                self._convert_indeterminate(ffmpeg, encode_args)
            else:
                self._convert_with_progress(ffmpeg, encode_args, duration_sec)

            if not self.isInterruptionRequested():
                self.progress.emit(100)
                self.status.emit(t("progress.convert_done"))
                self.finished.emit(True, self.output_path)
            else:
                self.finished.emit(False, t("status.cancelled"))

        except FileNotFoundError:
            self.log.emit(traceback.format_exc())
            self.finished.emit(False, "FFmpeg 未找到。请将 FFmpeg 安装到 D:\\CC_project\\transallum\\tools\\ffmpeg\\ 或系统 PATH。")
        except Exception as e:
            self.log.emit(traceback.format_exc())
            self.finished.emit(False, str(e))

    def _get_duration(self, ffprobe: str, filepath: str) -> float | None:
        """用 ffprobe 获取媒体时长（秒）"""
        try:
            result = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", filepath],
                capture_output=True, text=True, timeout=30, creationflags=_NO_WINDOW
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception:
            pass
        return None

    def _trim_start(self) -> list:
        """截取起始参数（置于 -i 之前，快速定位到 start_time）。"""
        return ["-ss", str(self.start_time)] if self.start_time is not None else []

    def _trim_duration(self) -> list:
        """截取时长参数（置于 -i 之后，输出 end-start 秒）。"""
        if self.end_time is not None:
            base = self.start_time if self.start_time is not None else 0.0
            return ["-t", str(self.end_time - base)]
        return []

    def _has_audio_stream(self, ffprobe: str, filepath: str) -> bool:
        """检测源文件是否包含音频流。探测失败时返回 True（不拦截，交给 FFmpeg 报错）。"""
        try:
            result = subprocess.run(
                [ffprobe, "-v", "error", "-select_streams", "a",
                 "-show_entries", "stream=index", "-of", "csv=p=0", filepath],
                capture_output=True, text=True, timeout=30, creationflags=_NO_WINDOW
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            return True

    def _convert_with_progress(self, ffmpeg: str, encode_args: list, duration_sec: float):
        """带进度条的转换"""
        cmd = [ffmpeg, "-y"] + self._trim_start() + ["-i", self.input_path] \
              + self._trim_duration() + ["-progress", "pipe:1",
                                         "-nostats", "-loglevel", "error"] \
              + encode_args + [self.output_path]

        self.status.emit(t("progress.converting"))
        self.log.emit(t("log.cmd", cmd=" ".join(cmd)))

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", creationflags=_NO_WINDOW
        )

        for line in process.stdout:
            if self.isInterruptionRequested():
                process.terminate()
                return
            if line.startswith("out_time_us="):
                try:
                    time_us = int(line.split("=")[1].strip())
                    time_sec = time_us / 1_000_000
                    pct = min(int(time_sec / duration_sec * 100), 99)
                    self.progress.emit(pct)
                    self.status.emit(f"{t('progress.converting')} {pct}%")
                except (ValueError, IndexError):
                    pass

        process.wait()
        if process.returncode != 0 and not self.isInterruptionRequested():
            stderr = process.stderr.read()
            friendly = _friendly_ffmpeg_error(stderr)
            if friendly:
                raise RuntimeError(friendly)
            raise RuntimeError(f"FFmpeg 错误 (code={process.returncode}): {stderr[:500]}")

    def _convert_indeterminate(self, ffmpeg: str, encode_args: list):
        """无时长信息时的转换"""
        cmd = [ffmpeg, "-y"] + self._trim_start() + ["-i", self.input_path] \
              + self._trim_duration() + ["-loglevel", "error"] \
              + encode_args + [self.output_path]

        self.status.emit(t("progress.indeterminate"))
        self.log.emit(t("log.cmd", cmd=" ".join(cmd)))

        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", creationflags=_NO_WINDOW)
        if result.returncode != 0 and not self.isInterruptionRequested():
            friendly = _friendly_ffmpeg_error(result.stderr)
            if friendly:
                raise RuntimeError(friendly)
            raise RuntimeError(f"FFmpeg 错误: {result.stderr[:500]}")


# ─── 文档转换 Worker (PyMuPDF + pdfplumber, 纯 Python) ─────────

class DocumentConvertWorker(BaseWorker):
    """使用 PyMuPDF / pdfplumber 进行 PDF → TXT/DOCX 转换"""

    def __init__(self, input_path: str, output_path: str,
                 output_format: str, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.output_format = output_format

    def run(self):
        try:
            self.status.emit(t("progress.doc_converting"))
            self.progress.emit(5)

            if self.isInterruptionRequested():
                self.finished.emit(False, t("status.cancelled"))
                return

            # 提取 PDF 文本
            text_by_page = self._extract_text()

            if self.isInterruptionRequested():
                self.finished.emit(False, t("status.cancelled"))
                return

            self.progress.emit(85)
            self.status.emit(t("progress.saving"))

            # 写入输出
            _, out_ext = os.path.splitext(self.output_path)
            if out_ext.lower() == ".docx":
                self._write_docx(text_by_page)
            else:
                self._write_txt(text_by_page)

            self.progress.emit(100)
            self.status.emit(t("progress.doc_done"))
            self.finished.emit(True, self.output_path)

        except Exception as e:
            self.log.emit(traceback.format_exc())
            self.finished.emit(False, str(e))

    def _extract_text(self) -> list[tuple[int, str]]:
        """提取 PDF 每页文本，返回 [(页码, 文本), ...]"""
        self.log.emit("使用 pdfplumber 提取文本...")
        import pdfplumber

        pages = []
        with pdfplumber.open(self.input_path) as pdf:
            total = len(pdf.pages)
            self.log.emit(t("log.total_pages", n=total))

            for i, page in enumerate(pdf.pages):
                if self.isInterruptionRequested():
                    return pages

                pct = 10 + int((i + 1) / total * 70)
                self.progress.emit(pct)
                self.status.emit(f"{t('progress.ocr_page')}{i + 1}/{total}{t('progress.ocr_page_suffix')}")

                text = page.extract_text()
                if text:
                    pages.append((i + 1, text.strip()))
                else:
                    pages.append((i + 1, ""))

        return pages

    def _write_txt(self, pages: list[tuple[int, str]]):
        """写纯文本"""
        with open(self.output_path, "w", encoding="utf-8") as f:
            for page_num, text in pages:
                f.write(f"--- 第 {page_num} 页 ---\n")
                f.write(text + "\n\n")

    def _write_docx(self, pages: list[tuple[int, str]]):
        """写 Word 文档"""
        from docx import Document
        from docx.shared import Pt

        doc = Document()
        # 设置默认字体
        style = doc.styles["Normal"]
        style.font.size = Pt(11)

        for page_num, text in pages:
            doc.add_heading(f"第 {page_num} 页", level=2)
            for para_text in text.split("\n"):
                if para_text.strip():
                    doc.add_paragraph(para_text.strip())
            doc.add_page_break()

        doc.save(self.output_path)


# ─── OCR Worker ──────────────────────────────────────────────────

class OCRWorker(BaseWorker):
    """使用 Tesseract OCR 对扫描型 PDF 执行文字识别"""

    def __init__(self, input_path: str, output_path: str,
                 output_format: str, language: str = "chi_sim+eng", parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.output_format = output_format
        self.language = language

    def run(self):
        try:
            import fitz  # PyMuPDF
            import pytesseract

            from utils.config import find_exe

            # 指定 D 盘 Tesseract 路径
            tesseract_exe = find_exe("tesseract")
            if tesseract_exe:
                pytesseract.pytesseract.tesseract_cmd = tesseract_exe
                self.log.emit(f"Tesseract: {tesseract_exe}")

            self.status.emit(t("progress.pdf_to_image"))
            self.progress.emit(2)

            # 用 PyMuPDF 渲染 PDF 为图片
            doc = fitz.open(self.input_path)
            total_pages = len(doc)
            self.log.emit(t("log.total_pages", n=total_pages))

            if self.isInterruptionRequested():
                doc.close()
                self.finished.emit(False, t("status.cancelled"))
                return

            all_text = []
            for i in range(total_pages):
                if self.isInterruptionRequested():
                    doc.close()
                    self.finished.emit(False, t("status.cancelled"))
                    return

                pct = 5 + int((i + 1) / total_pages * 85)
                self.progress.emit(pct)
                self.status.emit(
                    f"{t('progress.ocr_page')}{i + 1}/{total_pages}{t('progress.ocr_page_suffix')}")

                # 渲染页面为 300 DPI 图片
                page = doc[i]
                mat = fitz.Matrix(300/72, 300/72)
                pix = page.get_pixmap(matrix=mat)
                from PIL import Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Tesseract OCR
                text = pytesseract.image_to_string(img, lang=self.language)
                all_text.append(f"--- 第 {i + 1} 页 ---\n{text}\n")

            doc.close()

            self.progress.emit(92)
            self.status.emit(t("progress.saving"))

            if self.output_format == ".docx":
                from docx import Document
                doc = Document()
                for page_text in all_text:
                    doc.add_paragraph(page_text)
                doc.save(self.output_path)
            else:
                with open(self.output_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(all_text))

            self.progress.emit(100)
            self.status.emit(f"{t('progress.ocr_done')}{total_pages}{t('progress.ocr_pages')}")
            self.finished.emit(True, self.output_path)

        except Exception as e:
            self.log.emit(traceback.format_exc())
            self.finished.emit(False, str(e))


# ─── AI 听写 Worker ──────────────────────────────────────────────

class TranscribeWorker(BaseWorker):
    """使用 faster-whisper 进行语音转文字，长音频自动分段"""

    CHUNK_SECONDS = 30   # Whisper 原生训练长度，最佳准确率
    OVERLAP_SECONDS = 2  # 段间重叠，防止边界断词

    def __init__(self, input_path: str, output_path: str,
                 output_format: str = ".txt", model_size: str = "tiny",
                 language: str | None = None, device_pref: str = "auto", parent=None):
        """
        device_pref: "auto" → 有 GPU 用 GPU，否则 CPU
                     "cpu"  → 强制 CPU
                     "cuda" → 优先 GPU，不可用时回退 CPU
        """
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.output_format = output_format
        self.model_size = model_size
        self.language = language
        self.device_pref = device_pref or "auto"
        self._temp_dir = None

    def run(self):
        """主流程：准备环境 → 分段 → 选设备 → 加载模型 → 逐段识别 → 输出"""
        try:
            from utils.config import (
                PROJECT_ROOT,
                WHISPER_MODELS_DIR,
                detect_gpu,
                find_exe,
                setup_whisper_env,
            )
            _diag("===== TranscribeWorker 开始 =====")
            _diag(f"model_size={self.model_size}  input={self.input_path}")
            _diag(f"PROJECT_ROOT={PROJECT_ROOT}")
            _diag(f"WHISPER_MODELS_DIR={WHISPER_MODELS_DIR}")

            setup_whisper_env()   # HF 缓存重定向到 D 盘，须先于 faster_whisper 导入
            _diag("导入 faster_whisper 开始…")
            from faster_whisper import WhisperModel
            _diag("faster_whisper 导入完成")

            ffmpeg = find_exe("ffmpeg") or "ffmpeg"
            ffprobe = find_exe("ffprobe") or "ffprobe"

            self.status.emit(f"{t('progress.loading_model')} ({self.model_size})...")
            self.progress.emit(1)

            # ── 获取音频时长 + 分段策略 ──
            total_sec = self._get_duration(ffprobe, self.input_path) or 0
            if total_sec:
                self.log.emit(f"音频时长: {int(total_sec // 60)}分"
                              f"{int(total_sec % 60)}秒 ({total_sec:.0f}s)")
            chunks = self._plan_chunks(ffmpeg, total_sec)

            # ── 解析加速设备 ──
            _diag("detect_gpu() 调用前")
            gpu_ok = detect_gpu()
            device, compute_type = self._resolve_device(gpu_ok)
            if device == "cuda":
                self.log.emit("⚡ GPU 加速已启用 (CUDA, float16)")
            else:
                self.log.emit("使用 CPU 推理 (int8)")
            self.log.emit(t("log.device", device=device, compute=compute_type))
            _diag(f"device_pref={self.device_pref} gpu_ok={gpu_ok} → device={device} compute={compute_type}")

            # ── 加载模型（本地优先，缺失时联网下载） ──
            model = self._load_model(WhisperModel, device, compute_type, WHISPER_MODELS_DIR)

            if self.isInterruptionRequested():
                self._cancel()
                return

            # ── 逐段识别 ──
            results = self._transcribe_chunks(model, chunks)
            if results is None:      # 已取消
                return
            self._cleanup()

            # ── 按格式输出 ──
            self.progress.emit(95)
            self.status.emit(t("progress.saving"))
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(self._format_output(results))

            self.progress.emit(100)
            duration_min = total_sec / 60 if total_sec > 0 else 0
            self.status.emit(f"{t('progress.transcribe_done')} "
                             f"{duration_min:.1f}min → {len(results)} segments")
            self.finished.emit(True, self.output_path)

        except Exception as e:
            self._cleanup()
            _diag(f"[TranscribeWorker] 转换异常: {type(e).__name__}: {e}")
            _diag(traceback.format_exc())
            self.log.emit(traceback.format_exc())
            self.finished.emit(False, str(e))

    # ── 分段策略 ──

    def _plan_chunks(self, ffmpeg: str, total_sec: float) -> list:
        """分段策略：长音频自动切分，否则整段识别。返回 [(路径, 时间偏移)]"""
        if total_sec > self.CHUNK_SECONDS:
            chunks = self._split_audio(ffmpeg, total_sec)
            self.log.emit(f"长音频检测 → 自动切分为 {len(chunks)} 段 (~{self.CHUNK_SECONDS}s/段)")
            return chunks
        return [(self.input_path, 0.0)]  # (路径, 时间偏移)

    # ── 设备解析 ──

    def _resolve_device(self, gpu_ok: bool) -> tuple[str, str]:
        """根据用户偏好与 GPU 可用性决定 (device, compute_type)。"""
        if self.device_pref == "cuda":
            if gpu_ok:
                return "cuda", "float16"
            self.log.emit("⚠ GPU 不可用，自动回退到 CPU…")
            return "cpu", "int8"
        if self.device_pref == "cpu":
            return "cpu", "int8"
        return ("cuda", "float16") if gpu_ok else ("cpu", "int8")

    # ── 模型加载 ──

    def _load_model(self, WhisperModel, device: str, compute_type: str, models_dir) -> object:
        """加载模型：优先本地目录，缺失时联网下载；失败给出清晰中文指引。"""
        from utils.config import resolve_whisper_model
        local_model = resolve_whisper_model(self.model_size)
        _diag(f"resolve_whisper_model('{self.model_size}') → {local_model}")
        try:
            if local_model:
                self.log.emit(f"使用本地模型: {local_model}")
                _diag(f"加载本地模型: {local_model}")
                model = WhisperModel(local_model, device=device,
                                     compute_type=compute_type,
                                     local_files_only=True)
                _diag("本地模型加载成功")
            else:
                self.log.emit(f"本地未找到 {self.model_size} 模型，尝试从网络下载…")
                _diag(f"本地无模型，尝试联网下载 {self.model_size}")
                model = WhisperModel(self.model_size, device=device,
                                     compute_type=compute_type,
                                     download_root=str(models_dir))
                _diag("联网下载/加载模型成功")
        except Exception as e:
            _diag(f"模型加载失败: {type(e).__name__}: {e}")
            _diag(traceback.format_exc())
            raise RuntimeError(
                f"无法加载模型 {self.model_size}。\n"
                f"本地模型不存在，且联网下载失败"
                f"（网络无法访问 Hugging Face / 模型未预下载）。\n"
                f"解决方法：运行 scripts\\download_whisper_model.py 预下载模型"
                f"（从魔搭镜像获取），完成后重新转换。\n"
                f"详情: {e}") from e
        return model

    # ── 逐段识别 ──

    def _transcribe_chunks(self, model, chunks) -> list | None:
        """逐段识别，带取消检查与进度上报；取消时返回 None。"""
        all_results = []
        total_chunks = len(chunks)

        for idx, (chunk_path, offset_sec) in enumerate(chunks):
            if self.isInterruptionRequested():
                self._cancel()
                return None

            chunk_pct_base = int(idx / total_chunks * 90)
            self.status.emit(f"[{idx + 1}/{total_chunks}] {t('progress.transcribing')}")

            segments, info = model.transcribe(
                chunk_path,
                language=self.language,
                beam_size=5,
                vad_filter=True,
            )

            if idx == 0:
                self.log.emit(t("log.lang_detected",
                                lang=info.language,
                                prob=info.language_probability))

            for seg in segments:
                if self.isInterruptionRequested():
                    self._cancel()
                    return None

                # 偏移时间戳
                seg = _OffsetSegment(seg, offset_sec)
                all_results.append(seg)

                # 更新进度
                chunk_progress = seg.end / self.CHUNK_SECONDS * (90 / total_chunks)
                pct = min(chunk_pct_base + int(chunk_progress), 95)
                self.progress.emit(pct)

            self.log.emit(f"  [{idx + 1}/{total_chunks}] {t('progress.ocr_page_suffix')} "
                          f"{len(all_results)} segments")

        return all_results

    # ── 取消 ──

    def _cancel(self):
        """取消任务：清理临时文件并发送取消信号。"""
        self._cleanup()
        self.finished.emit(False, t("status.cancelled"))

    # ── 输出格式 ──

    def _format_output(self, segments) -> str:
        """按输出格式生成文本内容"""
        if self.output_format == ".srt":
            return self._to_srt(segments)
        if self.output_format == ".vtt":
            return self._to_vtt(segments)
        return self._to_txt(segments)

    # ── 时长检测 ──

    def _get_duration(self, ffprobe: str, filepath: str) -> float | None:
        try:
            result = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", filepath],
                capture_output=True, text=True, timeout=30, creationflags=_NO_WINDOW
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception:
            pass
        return None

    # ── 音频切分 ──

    def _split_audio(self, ffmpeg: str, total_sec: float) -> list:
        """用 ffmpeg 将长音频切分为多个短文件，段间 2s 重叠防止断词。
        返回 [(chunk_path, offset_sec), ...]"""
        import tempfile
        self._temp_dir = tempfile.mkdtemp(prefix="transallum_")

        chunks = []
        start = 0.0
        idx = 0
        while start < total_sec:
            chunk_path = os.path.join(self._temp_dir, f"chunk_{idx:04d}.wav")
            # 每段 = CHUNK_SECONDS + 重叠部分（除最后一段）
            duration = min(self.CHUNK_SECONDS + self.OVERLAP_SECONDS, total_sec - start)
            subprocess.run(
                [ffmpeg, "-y", "-ss", str(start), "-i", self.input_path,
                 "-t", str(duration), "-c:a", "pcm_s16le", "-ar", "16000",
                 "-ac", "1", "-loglevel", "error", chunk_path],
                capture_output=True, timeout=120, creationflags=_NO_WINDOW
            )
            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                chunks.append((chunk_path, start))
            # 下一段从 CHUNK_SECONDS 处开始（不是 duration，因为有重叠）
            start += self.CHUNK_SECONDS
            idx += 1

        return chunks

    def _cleanup(self):
        """删除临时分段文件"""
        if self._temp_dir and os.path.isdir(self._temp_dir):
            import shutil
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass

    # ── 输出格式 ──

    def _format_time(self, seconds: float, fmt: str = "srt") -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds * 1000) % 1000)
        if fmt == "vtt":
            return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _to_txt(self, segments) -> str:
        return "\n".join([seg.text.strip() for seg in segments])

    def _to_srt(self, segments) -> str:
        lines = []
        for i, seg in enumerate(segments, 1):
            start = self._format_time(seg.start, "srt")
            end = self._format_time(seg.end, "srt")
            lines.append(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n")
        return "\n".join(lines)

    def _to_vtt(self, segments) -> str:
        lines = ["WEBVTT\n"]
        for seg in segments:
            start = self._format_time(seg.start, "vtt")
            end = self._format_time(seg.end, "vtt")
            lines.append(f"{start} --> {end}\n{seg.text.strip()}\n")
        return "\n".join(lines)


class _OffsetSegment:
    """带时间偏移的 segment 包装器"""

    def __init__(self, segment, offset: float):
        self._seg = segment
        self._offset = offset

    @property
    def start(self):
        return self._seg.start + self._offset

    @property
    def end(self):
        return self._seg.end + self._offset

    @property
    def text(self):
        return self._seg.text
