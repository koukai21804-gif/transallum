"""Transallum 主界面 — 万能转换器 · 双语 + 主题切换"""
import os
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QFont,
)
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.background import AppBackground, SidebarBackground
from gui.theme_settings_dialog import ThemeSettingsDialog
from gui.workers import (
    DocumentConvertWorker,
    MediaConvertWorker,
    OCRWorker,
    TranscribeWorker,
)
from utils.config import (
    DOC_FORMATS,
    MEDIA_FORMATS,
    OCR_FORMATS,
    TRANSCRIBE_FORMATS,
    WHISPER_MODELS,
    parse_time,
)
from utils.i18n import i18n, t
from utils.theme_settings import load_settings, merge_colors, save_settings
from utils.themes import DARK, LIGHT, build_stylesheet

# 当前激活主题色彩字典（初始深色；toggle_theme 更新）
_current_colors = DARK

# ═══════════════════════════════════════════════════════════════════
# 拖放输入框
# ═══════════════════════════════════════════════════════════════════

class DropLineEdit(QLineEdit):
    fileDropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        self._update_placeholder()

    def _update_placeholder(self):
        self.setPlaceholderText(t("input.placeholder"))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                border: 2px dashed {_current_colors['border_focus']};
                border-radius: 8px;
                background-color: {_current_colors['drag_glow']};
                color: {_current_colors['primary_hi']};
                padding: 10px 14px;
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.setText(path)
            self.fileDropped.emit(path)


# ═══════════════════════════════════════════════════════════════════
# 状态指示器
# ═══════════════════════════════════════════════════════════════════

def make_status_label(tool_name: str) -> QLabel:
    lbl = QLabel()
    lbl.setTextFormat(Qt.TextFormat.RichText)
    _render_status(lbl, tool_name, None)
    return lbl


def _render_status(lbl: QLabel, tool_name: str, available: bool | None):
    if available is True:
        color = _current_colors["green"]
        dot = f"<span style='color:{color};'>●</span>"
        text = f"  {dot}  {tool_name}: {t('tools.installed')}"
        style = f"font-size: 11px; color: {color}; font-weight: 600; background: transparent; padding: 2px 4px;"
    elif available is False:
        color = _current_colors["red"]
        dot = f"<span style='color:{color};'>●</span>"
        text = f"  {dot}  {tool_name}: {t('tools.notfound')}"
        style = f"font-size: 11px; color: {color}; font-weight: 600; background: transparent; padding: 2px 4px;"
    else:
        color = _current_colors["text_hint"]
        dot = f"<span style='color:{color};'>●</span>"
        text = f"  {dot}  {tool_name}: {t('tools.checking')}"
        style = f"font-size: 11px; color: {color}; background: transparent; padding: 2px 4px;"
    lbl.setText(text)
    lbl.setStyleSheet(style)


def update_status_label(lbl: QLabel, tool_name: str, available: bool, version: str = ""):
    _render_status(lbl, tool_name, available)
    if version:
        lbl.setToolTip(version[:60])


# ═══════════════════════════════════════════════════════════════════
# 转换页面基类
# ═══════════════════════════════════════════════════════════════════

class ConverterPage(QWidget):
    def __init__(self, title_key: str, icon: str,
                 input_formats: list, output_formats: list, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.title_icon = icon
        self.input_formats = input_formats
        self.output_formats = output_formats
        self.input_paths = []     # 批量：多个输入文件路径
        self.worker = None
        self._widgets_to_translate = []
        self.setup_ui()
        self.retranslate()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 28)
        layout.setSpacing(20)

        # 页面大标题
        self.title_lbl = QLabel()
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.DemiBold)
        self.title_lbl.setFont(title_font)
        self.title_lbl.setStyleSheet(f"color: {DARK['primary_hi']}; "
                                      f"padding-bottom: 2px; font-weight: 600;")
        layout.addWidget(self.title_lbl)
        self._widgets_to_translate.append(("title", self.title_lbl))

        # 输入文件
        self.input_group = QGroupBox()
        input_layout = QHBoxLayout(self.input_group)
        input_layout.setContentsMargins(16, 20, 16, 16)
        input_layout.setSpacing(12)
        self.file_input = DropLineEdit()
        self.file_input.setMinimumHeight(40)
        self.file_input.fileDropped.connect(self.on_file_selected)
        self.browse_btn = QPushButton()
        self.browse_btn.setObjectName("browseBtn")
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.clicked.connect(self.on_browse)
        input_layout.addWidget(self.file_input, 1)
        input_layout.addWidget(self.browse_btn)
        layout.addWidget(self.input_group)
        self._widgets_to_translate.append(("group", self.input_group))
        self._widgets_to_translate.append(("button", self.browse_btn, "input.browse"))

        # 输出设置
        self.output_group = QGroupBox()
        output_layout = QHBoxLayout(self.output_group)
        output_layout.setContentsMargins(16, 20, 16, 16)
        output_layout.setSpacing(12)

        self.fmt_label = QLabel()
        self.fmt_label.setStyleSheet(
            f"color: {_current_colors['text_hint']}; font-weight: 500; background: transparent;")
        output_layout.addWidget(self.fmt_label)
        self._widgets_to_translate.append(("label", self.fmt_label, "output.format"))

        self.format_combo = QComboBox()
        self.format_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.format_combo.setMinimumHeight(40)
        for fmt, label in self.get_format_items():
            self.format_combo.addItem(f"{label} ({fmt})", fmt)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        output_layout.addWidget(self.format_combo, 1)

        self.save_label = QLabel()
        self.save_label.setStyleSheet(
            f"color: {_current_colors['text_hint']}; font-weight: 500; background: transparent;")
        output_layout.addWidget(self.save_label)
        self._widgets_to_translate.append(("label", self.save_label, "output.save_to"))

        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        self.output_path.setMinimumHeight(40)
        output_layout.addWidget(self.output_path, 2)

        self.output_browse_btn = QPushButton()
        self.output_browse_btn.setObjectName("browseBtn")
        self.output_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.output_browse_btn.setMinimumHeight(40)
        self.output_browse_btn.clicked.connect(self.on_output_browse)
        output_layout.addWidget(self.output_browse_btn)
        self._widgets_to_translate.append(("button", self.output_browse_btn, "output.save_as"))

        layout.addWidget(self.output_group)
        self._widgets_to_translate.append(("group", self.output_group))

        # 操作按钮行
        btn_layout = QHBoxLayout()
        self.convert_btn = QPushButton()
        self.convert_btn.setObjectName("convertBtn")
        self.convert_btn.setEnabled(False)
        self.convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_btn.clicked.connect(self.on_convert)
        self._widgets_to_translate.append(("button", self.convert_btn, "btn.convert"))

        self.cancel_btn = QPushButton()
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.on_cancel)
        self._widgets_to_translate.append(("button", self.cancel_btn, "btn.cancel"))

        btn_layout.addWidget(self.convert_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 状态文字
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(
            f"color: {DARK['text_hint']}; font-size: 13px; padding: 2px 0;")
        layout.addWidget(self.status_lbl)

        # 日志终端
        self.log_group = QGroupBox()
        log_layout = QVBoxLayout(self.log_group)
        log_layout.setContentsMargins(4, 16, 4, 8)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(160)
        log_layout.addWidget(self.log_output)
        layout.addWidget(self.log_group)
        self._widgets_to_translate.append(("group", self.log_group))

        layout.addStretch()

    def retranslate(self):
        """刷新本页所有文本"""
        for item in self._widgets_to_translate:
            kind = item[0]
            if kind == "title":
                item[1].setText(f"{self.title_icon}  {t(self.title_key)}")
            elif kind == "group":
                # 通过 key 映射
                g = item[1]
                if g is self.input_group:
                    g.setTitle(t("input.group"))
                elif g is self.output_group:
                    g.setTitle(t("output.group"))
                elif g is self.log_group:
                    g.setTitle(t("log.group"))
            elif kind == "button" or kind == "label":
                item[1].setText(t(item[2]))
        # 更新 placeholder
        self.file_input._update_placeholder()
        self.output_path.setPlaceholderText(t("output.placeholder"))
        self.log_output.setPlaceholderText(t("log.placeholder"))

    # ── 格式条目（子类可覆盖）──
    def get_format_items(self) -> list:
        return [(fmt, fmt.upper().lstrip(".")) for fmt in self.output_formats]

    # ── 文件选择 ──
    def on_file_selected(self, path: str):
        """单文件拖放回调"""
        self.input_paths = [path]
        self.convert_btn.setEnabled(True)
        self._update_display_for_files()

    def on_browse(self):
        ext_filter = " ".join([f"*{e}" for e in self.input_formats])
        filter_str = f"{t('btn.file_filter')} ({ext_filter});;{t('btn.all_files')} (*.*)"
        paths, _ = QFileDialog.getOpenFileNames(self, t("dialog.select_file"), "", filter_str)
        if paths:
            self.input_paths = paths
            self._update_display_for_files()
            self.convert_btn.setEnabled(True)

    def _update_display_for_files(self):
        """根据选中的文件更新输入框显示"""
        n = len(self.input_paths)
        if n == 1:
            path = self.input_paths[0]
            self.file_input.setText(path)
            self.file_input.setToolTip(path)
            in_path = Path(path)
            # 若当前格式与源扩展名相同，自动切到下一个不同格式，避免覆盖源文件
            self._ensure_distinct_format(in_path.suffix)
            out_fmt = self.format_combo.currentData()
            out_path = in_path.with_suffix(out_fmt)
            self.output_path.setText(str(out_path))
            self.output_path.setToolTip(str(out_path))
            self.log(f"<span style='color:{_current_colors['green']};'>{t('log.ok')}</span> "
                     f"{t('log.selected_file', path=path)}")
        else:
            self.file_input.setText(f"📦  已选择 {n} 个文件（批量模式）")
            folder = os.path.dirname(self.input_paths[0])
            self.output_path.setText(f"{folder}  (输出至各文件同目录)")
            self.log(f"<span style='color:{_current_colors['primary_hi']};'>[BATCH]</span> {n} 个文件")

    def _ensure_distinct_format(self, src_ext: str):
        """若当前输出格式与源扩展名相同，自动切换到第一个不同的格式（防覆盖源文件）。"""
        src_ext = src_ext.lower()
        if self.format_combo.currentData() == src_ext:
            for i in range(self.format_combo.count()):
                if self.format_combo.itemData(i) != src_ext:
                    self.format_combo.setCurrentIndex(i)
                    return

    def _on_format_changed(self, idx):
        """切换输出格式时，自动刷新单文件的输出路径。"""
        if len(self.input_paths) == 1:
            in_path = Path(self.input_paths[0])
            out_fmt = self.format_combo.currentData()
            if out_fmt:
                self.output_path.setText(str(in_path.with_suffix(out_fmt)))

    def on_output_browse(self):
        out_fmt = self.format_combo.currentData()
        filter_str = f"{out_fmt.upper()} (*{out_fmt});;{t('btn.all_files')} (*.*)"
        path, _ = QFileDialog.getSaveFileName(self, t("dialog.save_as"), "", filter_str)
        if path:
            self.output_path.setText(path)
            self.output_path.setToolTip(path)

    def on_convert(self):
        pass

    def on_cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log(t("log.warn_cancel"))

    def set_converting(self, active: bool):
        self.convert_btn.setVisible(not active)
        self.cancel_btn.setVisible(active)
        self.progress_bar.setVisible(active)
        self.file_input.setEnabled(not active)
        self.browse_btn.setEnabled(not active)
        self.format_combo.setEnabled(not active)
        self.output_browse_btn.setEnabled(not active)
        if active:
            self.progress_bar.setValue(0)

    def on_progress(self, value: int):
        self.progress_bar.setValue(value)

    def on_status(self, text: str):
        self.status_lbl.setText(text)

    def on_finished(self, success: bool, message: str):
        self.set_converting(False)
        if success:
            self.progress_bar.setValue(100)
            self.status_lbl.setText(t("status.done"))
            self.log(f"<span style='color:{_current_colors['green']};'>{t('log.ok')}</span> "
                     f"{t('log.success', path=message)}")
            QMessageBox.information(self, t("dialog.done_title"),
                                    f"{t('dialog.done_msg')}{message}")
        else:
            self.status_lbl.setText(t("status.failed"))
            self.log(f"<span style='color:{_current_colors['red']};'>{t('log.err')}</span> "
                     f"{t('log.failed', msg=message)}")
            if message != t("status.cancelled"):
                QMessageBox.warning(self, t("dialog.fail_title"),
                                    f"{t('dialog.fail_msg')}{message}")

    def _build_batch_tasks(self) -> list:
        """根据 input_paths 构建批量任务列表。子类需覆盖此方法。
        返回: [(input_path, output_path, WorkerClass, kwargs_dict), ...]"""
        out_fmt = self.format_combo.currentData()
        tasks = []
        for p in self.input_paths:
            out = str(Path(p).with_suffix(out_fmt))
            tasks.append((p, out, None, {}))
        return tasks

    def _run_batch(self, tasks: list):
        """启动批量转换"""
        from gui.workers import BatchWorker
        self.set_converting(True)
        self.log(self._sep())
        n = len(tasks)
        self.log(f"<span style='color:{_current_colors['primary_hi']};'>[BATCH] {n} 个文件</span>")

        self.worker = BatchWorker(tasks)
        self.worker.file_index.connect(
            lambda cur, total: self.log(
                f"<span style='color:{_current_colors['primary_hi']};'>── [{cur}/{total}]</span>"))
        self.worker.file_progress.connect(self.on_progress)
        self.worker.progress.connect(self.on_progress)
        self.worker.status.connect(self.on_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.log.connect(self.log)
        self.worker.start()

    def log(self, text: str):
        if "<span" not in text:
            lo = text.lower()
            if text.startswith("[OK]") or "✅" in text:
                color = _current_colors["green"]
            elif "[WARN]" in text or "⚠" in text or lo.startswith("warning"):
                color = _current_colors["warning"]
            elif text.startswith("[ERR]") or "❌" in text or lo.startswith("error"):
                color = _current_colors["red"]
            else:
                color = _current_colors["text_hint"]
            text = f"<span style='color:{color};'>{text}</span>"
        self.log_output.append(text)
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _sep(self):
        return f"<span style='color:{_current_colors['text_hint']};'>{'─' * 52}</span>"


# ═══════════════════════════════════════════════════════════════════
# 1. 音视频互转
# ═══════════════════════════════════════════════════════════════════

class MediaPage(ConverterPage):
    def __init__(self, parent=None):
        all_in = MEDIA_FORMATS["video"]["input"] + MEDIA_FORMATS["audio"]["input"]
        all_out = MEDIA_FORMATS["video"]["output"] + MEDIA_FORMATS["audio"]["output"]
        super().__init__("page.media", "🎬", all_in, all_out, parent)
        self.setup_media_options()
        self.retranslate()  # 补译媒体特有控件

    def setup_media_options(self):
        """媒体页特有：截取片段控件"""
        ly = self.layout()
        self.trim_group = QGroupBox()
        trim_layout = QHBoxLayout(self.trim_group)
        trim_layout.setContentsMargins(16, 20, 16, 16)
        trim_layout.setSpacing(12)

        self.trim_enable = QCheckBox()
        self.trim_enable.setCursor(Qt.CursorShape.PointingHandCursor)
        self.trim_enable.setMinimumHeight(40)
        self.trim_enable.toggled.connect(self._on_trim_toggled)
        trim_layout.addWidget(self.trim_enable)

        self.trim_start_label = QLabel()
        self.trim_start_label.setStyleSheet(
            f"color: {_current_colors['text_hint']}; font-weight: 500; background: transparent;")
        trim_layout.addWidget(self.trim_start_label)

        self.trim_start_edit = QLineEdit()
        self.trim_start_edit.setPlaceholderText("00:00:24")
        self.trim_start_edit.setMinimumHeight(40)
        self.trim_start_edit.setMaximumWidth(140)
        trim_layout.addWidget(self.trim_start_edit)

        self.trim_end_label = QLabel()
        self.trim_end_label.setStyleSheet(
            f"color: {_current_colors['text_hint']}; font-weight: 500; background: transparent;")
        trim_layout.addWidget(self.trim_end_label)

        self.trim_end_edit = QLineEdit()
        self.trim_end_edit.setPlaceholderText("00:01:38")
        self.trim_end_edit.setMinimumHeight(40)
        self.trim_end_edit.setMaximumWidth(140)
        trim_layout.addWidget(self.trim_end_edit)

        self.trim_hint = QLabel()
        self.trim_hint.setStyleSheet(
            f"color: {_current_colors['text_hint']}; font-size: 12px; background: transparent;")
        trim_layout.addWidget(self.trim_hint)

        trim_layout.addStretch()

        ly.insertWidget(ly.indexOf(self.status_lbl), self.trim_group)
        self._widgets_to_translate.append(("group", self.trim_group, "media.trim"))
        self._widgets_to_translate.append(("button", self.trim_enable, "media.trim_enable"))
        self._widgets_to_translate.append(("label", self.trim_start_label, "media.trim_start"))
        self._widgets_to_translate.append(("label", self.trim_end_label, "media.trim_end"))
        self._widgets_to_translate.append(("label", self.trim_hint, "media.trim_hint"))

        # 初始：未启用截取，时间输入框禁用
        self.trim_start_edit.setEnabled(False)
        self.trim_end_edit.setEnabled(False)

    def _on_trim_toggled(self, checked):
        self.trim_start_edit.setEnabled(checked)
        self.trim_end_edit.setEnabled(checked)

    def get_format_items(self):
        items = []
        for cat in ["video", "audio"]:
            for fmt in MEDIA_FORMATS[cat]["output"]:
                label = t(f"media.{cat}")
                items.append((fmt, f"[{label}] {fmt.upper().lstrip('.')}"))
        return items

    def on_convert(self):
        if len(self.input_paths) > 1:
            tasks = self._build_batch_tasks()
            self._run_batch(tasks)
            return
        inp = self.input_paths[0] if self.input_paths else self.file_input.text().strip()
        out = self.output_path.text().strip()
        fmt = self.format_combo.currentData()
        if not self._ok(inp, out): return

        # 截取片段：解析并校验开始/结束时间
        start_time = end_time = None
        if self.trim_enable.isChecked():
            start_time = parse_time(self.trim_start_edit.text())
            end_time = parse_time(self.trim_end_edit.text())
            if start_time is None or end_time is None or end_time <= start_time:
                QMessageBox.warning(self, t("dialog.fail_title"), t("media.trim_invalid"))
                return

        self._go(MediaConvertWorker(inp, out, fmt,
                                    start_time=start_time, end_time=end_time),
                 t("log.convert_start", tag=t("log.media"),
                   filename=os.path.basename(inp), fmt=fmt))

    def _build_batch_tasks(self):
        fmt = self.format_combo.currentData()
        tasks = []
        for p in self.input_paths:
            out = str(Path(p).with_suffix(fmt))
            tasks.append((p, out, MediaConvertWorker, {"output_format": fmt}))
        return tasks

    def _ok(self, inp, out):
        if not inp or not os.path.isfile(inp):
            QMessageBox.warning(self, t("dialog.fail_title"), t("dialog.no_input")); return False
        if not out:
            QMessageBox.warning(self, t("dialog.fail_title"), t("dialog.no_output")); return False
        return True

    def _go(self, worker, log_msg):
        self.set_converting(True)
        self.log(self._sep())
        self.log(f"<span style='color:{_current_colors['primary_hi']};'>{log_msg}</span>")
        self.worker = worker
        worker.progress.connect(self.on_progress)
        worker.status.connect(self.on_status)
        worker.finished.connect(self.on_finished)
        worker.log.connect(self.log)
        worker.start()


# ═══════════════════════════════════════════════════════════════════
# 2. PDF → 文档
# ═══════════════════════════════════════════════════════════════════

class DocumentPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__("page.document", "📄",
                         DOC_FORMATS["input"], DOC_FORMATS["output"], parent)

    def on_convert(self):
        if len(self.input_paths) > 1:
            self._run_batch(self._build_batch_tasks())
            return
        inp = self.input_paths[0] if self.input_paths else self.file_input.text().strip()
        out = self.output_path.text().strip()
        fmt = self.format_combo.currentData()
        if not self._ok(inp, out): return
        self._go(DocumentConvertWorker(inp, out, fmt),
                 t("log.convert_start", tag=t("log.doc"),
                   filename=os.path.basename(inp), fmt=fmt))

    def _build_batch_tasks(self):
        fmt = self.format_combo.currentData()
        return [(p, str(Path(p).with_suffix(fmt)), DocumentConvertWorker,
                 {"output_format": fmt}) for p in self.input_paths]

    def _ok(self, inp, out):
        if not inp or not os.path.isfile(inp):
            QMessageBox.warning(self, t("dialog.fail_title"), t("dialog.no_pdf")); return False
        if not out:
            QMessageBox.warning(self, t("dialog.fail_title"), t("dialog.no_output")); return False
        return True

    def _go(self, worker, log_msg):
        self.set_converting(True)
        self.log(self._sep())
        self.log(f"<span style='color:{_current_colors['primary_hi']};'>{log_msg}</span>")
        self.worker = worker
        worker.progress.connect(self.on_progress)
        worker.status.connect(self.on_status)
        worker.finished.connect(self.on_finished)
        worker.log.connect(self.log)
        worker.start()


# ═══════════════════════════════════════════════════════════════════
# 3. OCR
# ═══════════════════════════════════════════════════════════════════

class OCRPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__("page.ocr", "🔍",
                         OCR_FORMATS["input"], OCR_FORMATS["output"], parent)
        self._ocr_items = []
        self.setup_ocr_options()
        self.retranslate()  # 补译 OCR 特有控件

    def setup_ocr_options(self):
        self.ocr_opts = QGroupBox()
        opt_layout = QHBoxLayout(self.ocr_opts)
        opt_layout.setContentsMargins(16, 20, 16, 16)
        opt_layout.setSpacing(12)

        self.ocr_lang_label = QLabel()
        self.ocr_lang_label.setStyleSheet(
            f"color: {DARK['text_hint']}; font-weight: 500; background: transparent;")
        opt_layout.addWidget(self.ocr_lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_combo.setMinimumHeight(40)
        self._ocr_items = [
            ("ocr.chi_eng", "chi_sim+eng"),
            ("ocr.chi_sim", "chi_sim"),
            ("ocr.chi_tra", "chi_tra"),
            ("ocr.eng",     "eng"),
            ("ocr.jpn",     "jpn"),
            ("ocr.kor",     "kor"),
        ]
        for label_key, data in self._ocr_items:
            self.lang_combo.addItem(t(label_key), data)
        opt_layout.addWidget(self.lang_combo)
        opt_layout.addStretch()

        ly = self.layout()
        ly.insertWidget(ly.indexOf(self.status_lbl), self.ocr_opts)
        self._widgets_to_translate.append(("group", self.ocr_opts, "ocr.settings"))
        self._widgets_to_translate.append(("label", self.ocr_lang_label, "ocr.lang"))

    def retranslate(self):
        super().retranslate()
        if not hasattr(self, 'lang_combo'):
            return
        # 刷新 OCR 语言下拉
        self.lang_combo.blockSignals(True)
        current_data = self.lang_combo.currentData()
        self.lang_combo.clear()
        for label_key, data in self._ocr_items:
            self.lang_combo.addItem(t(label_key), data)
        idx = self.lang_combo.findData(current_data)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.blockSignals(False)

    def on_convert(self):
        if len(self.input_paths) > 1:
            self._run_batch(self._build_batch_tasks())
            return
        inp = self.input_paths[0] if self.input_paths else self.file_input.text().strip()
        out = self.output_path.text().strip()
        fmt = self.format_combo.currentData()
        lang = self.lang_combo.currentData()
        if not inp or not os.path.isfile(inp):
            QMessageBox.warning(self, t("dialog.fail_title"), t("dialog.no_pdf")); return
        if not out:
            QMessageBox.warning(self, t("dialog.fail_title"), t("dialog.no_output")); return
        self.set_converting(True)
        self.log(self._sep())
        self.log(f"<span style='color:{_current_colors['primary_hi']};'>"
                 f"{t('log.ocr_start', filename=os.path.basename(inp), fmt=fmt, lang=lang)}</span>")
        self.worker = OCRWorker(inp, out, fmt, language=lang)
        self.worker.progress.connect(self.on_progress)
        self.worker.status.connect(self.on_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.log.connect(self.log)
        self.worker.start()

    def _build_batch_tasks(self):
        fmt = self.format_combo.currentData()
        lang = self.lang_combo.currentData()
        return [(p, str(Path(p).with_suffix(fmt)), OCRWorker,
                 {"output_format": fmt, "language": lang}) for p in self.input_paths]


# ═══════════════════════════════════════════════════════════════════
# 4. AI 听写
# ═══════════════════════════════════════════════════════════════════

class TranscribePage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__("page.transcribe", "🎙",
                         TRANSCRIBE_FORMATS["input"], TRANSCRIBE_FORMATS["output"], parent)
        self._whisper_lang_items = []
        self.setup_transcribe_options()
        self.retranslate()  # 补译听写特有控件

    def setup_transcribe_options(self):
        ly = self.layout()
        self.whisper_opts = QGroupBox()
        opts_layout = QHBoxLayout(self.whisper_opts)
        opts_layout.setContentsMargins(16, 20, 16, 16)
        opts_layout.setSpacing(12)

        self.model_label = QLabel()
        self.model_label.setStyleSheet(
            f"color: {DARK['text_hint']}; font-weight: 500; background: transparent;")
        opts_layout.addWidget(self.model_label)

        self.model_combo = QComboBox()
        self.model_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_combo.setMinimumHeight(40)
        for name, info in WHISPER_MODELS.items():
            self.model_combo.addItem(
                f"  {name}  │  {info['size_mb']}MB  │  {info['accuracy']}  │  {info['speed']}",
                name
            )
        ti = self.model_combo.findData("tiny")
        if ti >= 0:
            self.model_combo.setCurrentIndex(ti)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        opts_layout.addWidget(self.model_combo, 1)

        self.lang_label = QLabel()
        self.lang_label.setStyleSheet(
            f"color: {DARK['text_hint']}; font-weight: 500; background: transparent;")
        opts_layout.addWidget(self.lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_combo.setMinimumHeight(40)
        self._whisper_lang_items = [
            ("whisper.auto", None), ("whisper.zh", "zh"), ("whisper.en", "en"),
            ("whisper.ja", "ja"), ("whisper.ko", "ko"),
            ("whisper.fr", "fr"), ("whisper.de", "de"),
        ]
        for label_key, data in self._whisper_lang_items:
            self.lang_combo.addItem(t(label_key), data)
        opts_layout.addWidget(self.lang_combo)

        # 加速设备选择
        self.device_label = QLabel()
        self.device_label.setStyleSheet(
            f"color: {DARK['text_hint']}; font-weight: 500; background: transparent;")
        opts_layout.addWidget(self.device_label)

        self.device_combo = QComboBox()
        self.device_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.device_combo.setMinimumHeight(40)
        self._whisper_device_items = [
            ("whisper.device_auto", "auto"),
            ("whisper.device_cpu", "cpu"),
            ("whisper.device_gpu", "cuda"),
        ]
        for label_key, data in self._whisper_device_items:
            self.device_combo.addItem(t(label_key), data)
        di = self.device_combo.findData("auto")
        if di >= 0:
            self.device_combo.setCurrentIndex(di)
        opts_layout.addWidget(self.device_combo)

        opts_layout.addStretch()

        ly.insertWidget(ly.indexOf(self.status_lbl), self.whisper_opts)
        self._widgets_to_translate.append(("group", self.whisper_opts, "whisper.settings"))
        self._widgets_to_translate.append(("label", self.model_label, "whisper.model"))
        self._widgets_to_translate.append(("label", self.lang_label, "whisper.lang"))
        self._widgets_to_translate.append(("label", self.device_label, "whisper.device"))

    def retranslate(self):
        super().retranslate()
        if not hasattr(self, 'lang_combo'):
            return
        # 刷新听写语言下拉
        self.lang_combo.blockSignals(True)
        cd = self.lang_combo.currentData()
        self.lang_combo.clear()
        for label_key, data in self._whisper_lang_items:
            self.lang_combo.addItem(t(label_key), data)
        idx = self.lang_combo.findData(cd)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.blockSignals(False)

        # 刷新加速设备下拉
        self.device_combo.blockSignals(True)
        dd = self.device_combo.currentData()
        self.device_combo.clear()
        for label_key, data in self._whisper_device_items:
            self.device_combo.addItem(t(label_key), data)
        idx = self.device_combo.findData(dd)
        if idx >= 0:
            self.device_combo.setCurrentIndex(idx)
        self.device_combo.blockSignals(False)

    def _on_model_changed(self, idx):
        model_name = self.model_combo.currentData()
        info = WHISPER_MODELS.get(model_name, {})
        if info.get("size_mb", 0) > 1000:
            self.log(f"<span style='color:#f59e0b;'>{t('log.warn')}</span> "
                     f"{t('log.warn_model_size', model=model_name, size=info['size_mb'])}")

    def on_convert(self):
        device_pref = self.device_combo.currentData()
        dev_name = t(f"whisper.device_{device_pref}")

        if len(self.input_paths) > 1:
            model_size = self.model_combo.currentData()
            model_info = WHISPER_MODELS.get(model_size, {})
            reply = QMessageBox.question(
                self, t("dialog.confirm_title"),
                f"批量转录 {len(self.input_paths)} 个文件\n\n"
                f"模型: {model_size} (~{model_info.get('size_mb', '?')}MB)\n"
                f"设备: {dev_name}\n"
                f"这可能需要较长时间。是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._run_batch(self._build_batch_tasks())
            return

        inp = self.input_paths[0] if self.input_paths else self.file_input.text().strip()
        out = self.output_path.text().strip()
        fmt = self.format_combo.currentData()
        model_size = self.model_combo.currentData()
        language = self.lang_combo.currentData()

        if not inp or not os.path.isfile(inp):
            QMessageBox.warning(self, t("dialog.fail_title"), t("dialog.no_media")); return
        if not out:
            QMessageBox.warning(self, t("dialog.fail_title"), t("dialog.no_output")); return

        model_info = WHISPER_MODELS.get(model_size, {})
        reply = QMessageBox.question(
            self, t("dialog.confirm_title"),
            t("dialog.confirm_msg",
              model=model_size, input=os.path.basename(inp),
              output=os.path.basename(out), size=model_info.get('size_mb', '?'),
              speed=model_info.get('speed', '?'),
              accuracy=model_info.get('accuracy', '?'),
              device=dev_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.set_converting(True)
        self.log(self._sep())
        self.log(f"<span style='color:{_current_colors['primary_hi']};'>"
                 f"{t('log.whisper_start', filename=os.path.basename(inp), fmt=fmt, model=model_size)}"
                 f"  |  {dev_name}</span>")
        self.worker = TranscribeWorker(inp, out, fmt,
                                       model_size=model_size, language=language,
                                       device_pref=device_pref)
        self.worker.progress.connect(self.on_progress)
        self.worker.status.connect(self.on_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.log.connect(self.log)
        self.worker.start()

    def _build_batch_tasks(self):
        fmt = self.format_combo.currentData()
        model_size = self.model_combo.currentData()
        language = self.lang_combo.currentData()
        device_pref = self.device_combo.currentData()
        return [(p, str(Path(p).with_suffix(fmt)), TranscribeWorker,
                 {"output_format": fmt, "model_size": model_size, "language": language,
                  "device_pref": device_pref})
                for p in self.input_paths]


# ═══════════════════════════════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self._theme_is_dark = bool(self.settings.get("dark", True))
        self.resize(1020, 720)
        self.setMinimumSize(860, 600)
        self.setup_ui()
        self.apply_theme()
        self.check_tools()
        self.retranslate()

    def setup_ui(self):
        central = AppBackground()
        self.central_bg = central
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ============================================================
        # 左侧导航栏
        # ============================================================
        sidebar = SidebarBackground()
        self.sidebar_bg = sidebar
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 18, 14, 22)
        sidebar_layout.setSpacing(4)

        # --- 切换按钮栏（右对齐） ---
        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 0, 0, 0)

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("toolbarBtn")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)

        self.theme_settings_btn = QPushButton()
        self.theme_settings_btn.setObjectName("toolbarBtn")
        self.theme_settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_settings_btn.clicked.connect(self.open_theme_settings)

        self.lang_btn = QPushButton()
        self.lang_btn.setObjectName("toolbarBtn")
        self.lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_btn.clicked.connect(self.toggle_language)

        toggle_row.addStretch()
        toggle_row.addWidget(self.theme_btn)
        toggle_row.addWidget(self.theme_settings_btn)
        toggle_row.addWidget(self.lang_btn)
        sidebar_layout.addLayout(toggle_row)
        sidebar_layout.addSpacing(8)

        # --- 品牌区 ---
        self.brand_lbl = QLabel()
        brand_font = QFont()
        brand_font.setPointSize(17)
        brand_font.setBold(True)
        self.brand_lbl.setFont(brand_font)
        self.brand_lbl.setStyleSheet(
            f"color: {DARK['primary_hi']}; padding: 14px 8px 2px 8px; "
            f"background: transparent; font-weight: 700;"
        )
        sidebar_layout.addWidget(self.brand_lbl)

        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.3); font-size: 11px; "
            "padding: 0 8px 20px 8px; background: transparent;"
        )
        sidebar_layout.addWidget(self.subtitle_lbl)

        # 分隔线
        sep = QFrame()
        sep.setObjectName("sepLine")
        sep.setFrameShape(QFrame.Shape.HLine)
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(10)

        # --- 导航项 ---
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []

        nav_keys = ["nav.media", "nav.document", "nav.ocr", "nav.transcribe"]
        for idx, key in enumerate(nav_keys):
            btn = QPushButton(t(key))
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            self.nav_group.addButton(btn, idx)
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append((btn, key))

        sidebar_layout.addSpacing(18)

        # --- 工具状态卡片 ---
        self.tools_card = QFrame()
        self.tools_card.setObjectName("toolsCard")
        tools_layout = QVBoxLayout(self.tools_card)
        tools_layout.setContentsMargins(14, 14, 14, 14)
        tools_layout.setSpacing(8)

        self.tools_title = QLabel(t("tools.title"))
        self.tools_title.setStyleSheet(
            f"color: {DARK['text_hint']}; font-size: 11px; font-weight: 600; "
            f"background: transparent; padding-bottom: 4px;"
        )
        tools_layout.addWidget(self.tools_title)

        self.tool_labels = {}
        self._tool_states = {}  # {name: (available, version)} — refreshed in check_tools
        for tool in ["ffmpeg", "tesseract"]:
            lbl = make_status_label(tool)
            tools_layout.addWidget(lbl)
            self.tool_labels[tool] = lbl

        sidebar_layout.addWidget(self.tools_card)
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        # ============================================================
        # 右侧内容区
        # ============================================================
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")
        self.pages = [
            MediaPage(),
            DocumentPage(),
            OCRPage(),
            TranscribePage(),
        ]
        for page in self.pages:
            self.stack.addWidget(page)
        main_layout.addWidget(self.stack, 1)

        self.nav_buttons[0][0].setChecked(True)

    # ── 页面切换 ──
    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)

    # ── 主题应用（唯一入口） ──
    def apply_theme(self):
        global _current_colors
        base = DARK if self._theme_is_dark else LIGHT
        colors = merge_colors(base, self.settings.get("colors", {}))
        _current_colors = colors
        sheet = build_stylesheet(colors)
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        app.setStyleSheet(sheet)
        # 同步 palette
        from PyQt6.QtGui import QColor, QPalette
        p = app.palette()
        p.setColor(QPalette.ColorRole.Window, QColor(colors['bg_deep']))
        p.setColor(QPalette.ColorRole.WindowText, QColor(colors['text_body']))
        p.setColor(QPalette.ColorRole.Base, QColor(colors['bg_input']))
        p.setColor(QPalette.ColorRole.Text, QColor(colors['text_body']))
        p.setColor(QPalette.ColorRole.Button, QColor(colors['border_ctrl']))
        p.setColor(QPalette.ColorRole.ButtonText, QColor(colors['text_body']))
        app.setPalette(p)
        self._update_theme_widgets(colors)
        self._apply_background()
        self.retranslate()
        self.repaint()
        app.processEvents()

    def _apply_background(self):
        bg = self.settings.get("background", {})
        win = bg.get("window", {})
        side = bg.get("sidebar", {})
        c = _current_colors
        self.central_bg.set_background(c["bg_deep"], win.get("image"),
                                       float(win.get("opacity", 1.0)))
        self.sidebar_bg.set_background(c["bg_sidebar"], side.get("image"),
                                       float(side.get("opacity", 1.0)))
        self.sidebar_bg.set_border(c["border_ctrl"])

    def toggle_theme(self):
        self._theme_is_dark = not self._theme_is_dark
        self.settings["dark"] = self._theme_is_dark
        save_settings(self.settings)
        self.apply_theme()

    def open_theme_settings(self):
        base = DARK if self._theme_is_dark else LIGHT
        dlg = ThemeSettingsDialog(base, self.settings.get("colors", {}),
                                  self.settings.get("background", {}), self)
        if dlg.exec():
            data = dlg.result_data()
            self.settings["colors"] = data["colors"]
            self.settings["background"] = data["background"]
            save_settings(self.settings)
            self.apply_theme()

    def _update_theme_widgets(self, c: dict):
        """更新非样式表控制的 widget 内联样式"""
        drag_style = (
            f"border: 2px dashed {c['border_focus']}; border-radius: 8px; "
            f"background-color: {c['drag_glow']}; color: {c['primary_hi']}; padding: 10px 14px;"
        )
        for page in self.pages:
            # 页面背景（实际底色由 AppBackground 背景层绘制）
            page.setStyleSheet("background-color: transparent;")
            page.title_lbl.setStyleSheet(
                f"color: {c['primary_hi']}; padding-bottom: 2px; font-weight: 600; background: transparent;")
            page.fmt_label.setStyleSheet(
                f"color: {c['text_hint']}; font-weight: 500; background: transparent;")
            page.save_label.setStyleSheet(
                f"color: {c['text_hint']}; font-weight: 500; background: transparent;")
            page.status_lbl.setStyleSheet(
                f"color: {c['text_hint']}; font-size: 13px; padding: 2px 0; background: transparent;")
            # 拖放输入框记录拖拽样式（恢复清空；实际拖拽时用 _current_colors 动态生成）
            page.file_input._drag_style = drag_style
            # OCR / Transcribe 子控件
            if hasattr(page, 'ocr_lang_label'):
                page.ocr_lang_label.setStyleSheet(
                    f"color: {c['text_hint']}; font-weight: 500; background: transparent;")
            if hasattr(page, 'model_label'):
                page.model_label.setStyleSheet(
                    f"color: {c['text_hint']}; font-weight: 500; background: transparent;")
            if hasattr(page, 'lang_label'):
                page.lang_label.setStyleSheet(
                    f"color: {c['text_hint']}; font-weight: 500; background: transparent;")
            # MediaPage trim 标签
            if hasattr(page, 'trim_start_label'):
                page.trim_start_label.setStyleSheet(
                    f"color: {c['text_hint']}; font-weight: 500; background: transparent;")
            if hasattr(page, 'trim_end_label'):
                page.trim_end_label.setStyleSheet(
                    f"color: {c['text_hint']}; font-weight: 500; background: transparent;")
            if hasattr(page, 'trim_hint'):
                page.trim_hint.setStyleSheet(
                    f"color: {c['text_hint']}; font-size: 12px; background: transparent;")
            # 强制刷新页面及子控件
            page.repaint()

        self.brand_lbl.setStyleSheet(
            f"color: {c['primary_hi']}; padding: 14px 8px 2px 8px; "
            f"background: transparent; font-weight: 700;")
        opacity = "0.3" if self._theme_is_dark else "0.45"
        if self._theme_is_dark:
            self.subtitle_lbl.setStyleSheet(
                f"color: rgba(255,255,255,{opacity}); font-size: 11px; "
                f"padding: 0 8px 20px 8px; background: transparent;")
        else:
            self.subtitle_lbl.setStyleSheet(
                f"color: rgba(0,0,0,{opacity}); font-size: 11px; "
                f"padding: 0 8px 20px 8px; background: transparent;")
        self.tools_title.setStyleSheet(
            f"color: {c['text_hint']}; font-size: 11px; font-weight: 600; "
            f"background: transparent; padding-bottom: 4px;"
        )
        # 工具状态指示点颜色跟随主题
        for name, (available, version) in self._tool_states.items():
            lbl = self.tool_labels.get(name)
            if lbl:
                update_status_label(lbl, name, available, version)

    # ── 语言切换 ──
    def toggle_language(self):
        i18n.toggle()
        self.retranslate()
        for page in self.pages:
            page.retranslate()
        self.check_tools()

    # ── 刷新文本 ──
    def retranslate(self):
        self.setWindowTitle(t("window.title"))
        self.brand_lbl.setText(t("brand.name"))
        self.subtitle_lbl.setText(t("brand.subtitle"))
        self.tools_title.setText(t("tools.title"))
        self.theme_btn.setText(t("theme.light") if self._theme_is_dark else t("theme.dark"))
        self.theme_settings_btn.setText(t("theme.open"))
        self.lang_btn.setText(t("toggle.lang"))
        for btn, key in self.nav_buttons:
            btn.setText(t(key))

    # ── 工具检测 ──
    def check_tools(self):
        from utils.config import PROJECT_ROOT, TOOLS_DIR, check_all_tools
        tools = check_all_tools()
        # 在日志中显示路径信息（方便排查）
        self.pages[0].log(f"[TOOLS] PROJECT_ROOT={PROJECT_ROOT}")
        self.pages[0].log(f"[TOOLS] TOOLS_DIR={TOOLS_DIR} (exists={TOOLS_DIR.exists()})")
        for name, info in tools.items():
            lbl = self.tool_labels.get(name)
            if lbl:
                self._tool_states[name] = (info["available"], info.get("version", ""))
                update_status_label(lbl, name, info["available"], info.get("version", ""))
                if info["available"]:
                    self.pages[0].log(f"[TOOLS] {name}: {info['path']}")
                else:
                    self.pages[0].log(f"[TOOLS] {name}: NOT FOUND")


# ═══════════════════════════════════════════════════════════════════
# 模型设置对话框
# ═══════════════════════════════════════════════════════════════════

class ModelSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("model.dialog.title"))
        self.resize(520, 440)
        self.setStyleSheet(f"background-color: {DARK['bg_card']};")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel(t("model.dialog.title"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {DARK['text_title']}; background: transparent;")
        layout.addWidget(title)

        desc = QLabel(t("model.dialog.desc"))
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {DARK['text_hint']}; margin-bottom: 8px; background: transparent;")
        layout.addWidget(desc)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {DARK['border_card']}; border-radius: 8px; }}")
        sw = QWidget()
        sw.setStyleSheet(f"background-color: {DARK['bg_tools']};")
        sl = QVBoxLayout(sw)
        sl.setSpacing(6)

        self.model_checks = {}
        for name, info in WHISPER_MODELS.items():
            cb = QCheckBox(
                f"{name}  —  {info['size_mb']}MB  |  {info['accuracy']}  "
                f"|  速度: {info['speed']}  |  VRAM: ~{info['vram_gb']}GB"
            )
            sl.addWidget(cb)
            self.model_checks[name] = cb

        scroll.setWidget(sw)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        self.dl_btn = QPushButton(t("model.dialog.download"))
        self.dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dl_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DARK['primary']}; color: #ffffff; "
            f"padding: 10px 24px; border-radius: 8px; font-weight: 700; border: none; }}"
            f"QPushButton:hover {{ background-color: {DARK['primary_hi']}; }}"
        )
        self.dl_btn.clicked.connect(self.on_download)
        btn_layout.addWidget(self.dl_btn)
        btn_layout.addStretch()

        close_btn = QPushButton(t("model.dialog.close"))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DARK['border_ctrl']}; color: {DARK['text_body']}; "
            f"padding: 10px 24px; border-radius: 8px; font-weight: 600; "
            f"border: 1px solid {DARK['border_card']}; }}"
            f"QPushButton:hover {{ background-color: {DARK['border_card']}; "
            f"border-color: {DARK['primary_hi']}; }}"
        )
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def on_download(self):
        selected = [n for n, cb in self.model_checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.information(self, t("model.dialog.dl_title"),
                                    t("model.dialog.no_select"))
            return
        QMessageBox.information(
            self, t("model.dialog.dl_title"),
            t("model.dialog.dl_msg")
            + "\n".join([f"  • {m}" for m in selected])
            + t("model.dialog.dl_footer")
        )
        self.accept()
