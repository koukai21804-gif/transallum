"""国际化 — 中/英双语"""
from PyQt6.QtCore import QObject, pyqtSignal

TEXTS = {
    # ── 窗口 ──
    "window.title": {
        "zh": "Transallum — 万能转换器",
        "en": "Transallum — Universal Converter",
    },
    "brand.name": {
        "zh": "◈  Transallum",
        "en": "◈  Transallum",
    },
    "brand.subtitle": {
        "zh": "万能格式转换器",
        "en": "Universal Format Converter",
    },

    # ── 导航 ──
    "nav.media":     {"zh": "🎬   音视频互转",     "en": "🎬   Media Convert"},
    "nav.document":  {"zh": "📄   PDF → 文档",     "en": "📄   PDF → Doc"},
    "nav.ocr":       {"zh": "🔍   OCR 识别",       "en": "🔍   OCR"},
    "nav.transcribe":{"zh": "🎙   AI 听写",         "en": "🎙   Transcribe"},

    # ── 工具状态 ──
    "tools.title":   {"zh": "🔧  工具状态",        "en": "🔧  Tool Status"},
    "tools.installed":{"zh": "已安装",              "en": "installed"},
    "tools.notfound": {"zh": "未检测到",            "en": "not found"},
    "tools.checking": {"zh": "检测中...",           "en": "checking..."},

    # ── 页面标题 ──
    "page.media":       {"zh": "音视频格式互转",            "en": "Media Format Converter"},
    "page.document":    {"zh": "PDF → 文档互转",            "en": "PDF → Document"},
    "page.ocr":         {"zh": "图片型 PDF → 文字 (OCR)",   "en": "Scanned PDF → Text (OCR)"},
    "page.transcribe":  {"zh": "AI 听写 — 音视频 → 文字",   "en": "AI Transcribe — Media → Text"},

    # ── 输入文件 ──
    "input.group":      {"zh": "📥  输入文件",              "en": "📥  Input File"},
    "input.placeholder":{"zh": "📂  拖放文件到此处，或点击右侧 [浏览] 按钮...",
                         "en": "📂  Drop file here, or click [Browse]..."},
    "input.browse":     {"zh": "📂  浏览...",              "en": "📂  Browse..."},

    # ── 输出设置 ──
    "output.group":     {"zh": "📤  输出设置",             "en": "📤  Output Settings"},
    "output.format":    {"zh": "输出格式:",                "en": "Format:"},
    "output.save_to":   {"zh": "保存到:",                  "en": "Save to:"},
    "output.placeholder":{"zh": "自动生成（与输入同目录）...",
                          "en": "Auto-generated (same folder as input)..."},
    "output.save_as":   {"zh": "📁  另存为...",            "en": "📁  Save As..."},

    # ── 按钮 ──
    "btn.convert":      {"zh": "▶  开始转换",             "en": "▶  Convert"},
    "btn.cancel":       {"zh": "✕  取消转换",             "en": "✕  Cancel"},
    "btn.file_filter":  {"zh": "支持的格式",              "en": "Supported formats"},
    "btn.all_files":    {"zh": "所有文件",                "en": "All files"},

    # ── 日志 ──
    "log.group":        {"zh": "📋  转换日志",            "en": "📋  Log"},
    "log.placeholder":  {"zh": "$ 转换日志将显示在这里...", "en": "$ Log output will appear here..."},

    # ── 状态 ──
    "status.ready":     {"zh": "就绪",                    "en": "Ready"},
    "status.done":      {"zh": "✅ 转换完成！",           "en": "✅ Conversion complete!"},
    "status.failed":    {"zh": "❌ 转换失败",             "en": "❌ Conversion failed"},
    "status.converting":{"zh": "正在转换...",             "en": "Converting..."},
    "status.cancelling": {"zh": "正在取消...",            "en": "Cancelling..."},
    "status.cancelled":  {"zh": "用户取消了转换",          "en": "Cancelled by user"},

    # ── OCR 设置 ──
    "ocr.settings":     {"zh": "⚙  OCR 设置",            "en": "⚙  OCR Settings"},
    "ocr.lang":         {"zh": "识别语言:",               "en": "Language:"},
    "ocr.chi_eng":      {"zh": "中文 + 英文",             "en": "Chinese + English"},
    "ocr.chi_sim":      {"zh": "中文简体",                "en": "Chinese Simplified"},
    "ocr.chi_tra":      {"zh": "中文繁体",                "en": "Chinese Traditional"},
    "ocr.eng":          {"zh": "英文",                    "en": "English"},
    "ocr.jpn":          {"zh": "日文",                    "en": "Japanese"},
    "ocr.kor":          {"zh": "韩文",                    "en": "Korean"},

    # ── 听写设置 ──
    "whisper.settings": {"zh": "🤖  模型设置",            "en": "🤖  Model Settings"},
    "whisper.model":    {"zh": "Whisper 模型:",           "en": "Whisper Model:"},
    "whisper.lang":     {"zh": "语言:",                   "en": "Language:"},
    "whisper.auto":     {"zh": "自动检测",                "en": "Auto-detect"},
    "whisper.device":   {"zh": "加速设备:",               "en": "Acceleration:"},
    "whisper.device_auto": {"zh": "自动 (优先 GPU)",      "en": "Auto (GPU first)"},
    "whisper.device_cpu":  {"zh": "CPU",                 "en": "CPU"},
    "whisper.device_gpu":  {"zh": "GPU (CUDA)",          "en": "GPU (CUDA)"},
    "whisper.zh":       {"zh": "中文 (zh)",              "en": "Chinese (zh)"},
    "whisper.en":       {"zh": "英文 (en)",              "en": "English (en)"},
    "whisper.ja":       {"zh": "日文 (ja)",              "en": "Japanese (ja)"},
    "whisper.ko":       {"zh": "韩文 (ko)",              "en": "Korean (ko)"},
    "whisper.fr":       {"zh": "法文 (fr)",              "en": "French (fr)"},
    "whisper.de":       {"zh": "德文 (de)",              "en": "German (de)"},

    # ── 对话框 ──
    "error.no_audio_stream": {
        "zh": "源文件不包含音频流，无法转换为纯音频格式（mp3/wav/flac/aac/ogg 等）。\n\n"
              "源很可能是「静音录屏」或「纯视频文件」。\n"
              "如需提取声音，请确认录制时已开启麦克风/系统声音。",
        "en": "The source has no audio stream, so it cannot be converted to an audio-only "
              "format (mp3/wav/flac/aac/ogg...).\n\n"
              "The source is likely a muted screen recording or a video-only file.\n"
              "To extract sound, make sure the mic / system audio was enabled during recording."
    },
    "error.no_stream": {
        "zh": "源文件没有可编码的媒体流，FFmpeg 无法生成输出。\n"
              "如果目标是纯音频格式，通常是源视频本身不含音频轨道。",
        "en": "The source has no encodable media stream, so FFmpeg could not produce output.\n"
              "If the target is an audio-only format, the source video likely has no audio track."
    },
    "error.same_file": {
        "zh": "输出文件与源文件相同，已阻止覆盖！\n\n"
              "请选择不同的输出格式（如 mp4 → mp3），\n"
              "或点击「另存为」指定其他路径。",
        "en": "The output path is the same as the source — overwrite blocked!\n\n"
              "Please choose a different output format (e.g. mp4 → mp3),\n"
              "or use 'Save As' to specify another path."
    },
    "dialog.select_file":   {"zh": "选择文件",            "en": "Select File"},
    "dialog.save_as":       {"zh": "保存为",              "en": "Save As"},
    "dialog.done_title":    {"zh": "转换完成",            "en": "Conversion Complete"},
    "dialog.done_msg":      {"zh": "转换完成！\n\n输出文件:\n", "en": "Conversion complete!\n\nOutput:\n"},
    "dialog.fail_title":    {"zh": "转换失败",            "en": "Conversion Failed"},
    "dialog.fail_msg":      {"zh": "转换过程中出现错误:\n\n", "en": "Error during conversion:\n\n"},
    "dialog.no_input":      {"zh": "请先选择一个有效的输入文件。", "en": "Please select a valid input file."},
    "dialog.no_output":     {"zh": "请指定输出文件路径。",  "en": "Please specify an output path."},
    "dialog.no_pdf":        {"zh": "请先选择一个有效的 PDF 文件。", "en": "Please select a valid PDF file."},
    "dialog.no_media":      {"zh": "请先选择一个有效的音视频文件。", "en": "Please select a valid media file."},
    "dialog.confirm_title": {"zh": "确认转录",            "en": "Confirm Transcription"},
    "dialog.confirm_msg":   {
        "zh": "即将使用 {model} 模型进行转录：\n\n"
              "  📁  输入 : {input}\n"
              "  📝  输出 : {output}\n"
              "  🧠  模型 : {model}  (~{size}MB)\n"
              "  ⚡  速度 : {speed}\n"
              "  🎯  精度 : {accuracy}\n"
              "  ⚙️  设备 : {device}\n\n"
              "是否继续？",
        "en": "About to transcribe using {model} model:\n\n"
              "  📁  Input : {input}\n"
              "  📝  Output : {output}\n"
              "  🧠  Model : {model}  (~{size}MB)\n"
              "  ⚡  Speed : {speed}\n"
              "  🎯  Accuracy : {accuracy}\n"
              "  ⚙️  Device : {device}\n\n"
              "Continue?"
    },

    # ── 媒体格式标签 ──
    "media.video":  {"zh": "视频", "en": "Video"},
    "media.audio":  {"zh": "音频", "en": "Audio"},
    "media.trim":        {"zh": "✂  截取片段", "en": "✂  Trim Segment"},
    "media.trim_enable": {"zh": "启用截取", "en": "Enable Trim"},
    "media.trim_start":  {"zh": "开始时间:", "en": "Start:"},
    "media.trim_end":    {"zh": "结束时间:", "en": "End:"},
    "media.trim_hint":   {"zh": "格式：秒 / 分:秒 / 时:分:秒", "en": "Format: sec / mm:ss / hh:mm:ss"},
    "media.trim_invalid":{"zh": "截取时间无效：结束时间必须大于开始时间，且格式为「秒」或「分:秒」或「时:分:秒」。",
                          "en": "Invalid trim times — end must be greater than start, format sec / mm:ss / hh:mm:ss."},

    # ── 日志前缀 ──
    "log.ok":       {"zh": "[OK]",   "en": "[OK]"},
    "log.err":      {"zh": "[ERR]",  "en": "[ERR]"},
    "log.warn":     {"zh": "[WARN]", "en": "[WARN]"},
    "log.media":    {"zh": "[MEDIA]","en": "[MEDIA]"},
    "log.doc":      {"zh": "[DOC]",  "en": "[DOC]"},
    "log.ocr":      {"zh": "[OCR]",  "en": "[OCR]"},
    "log.whisper":  {"zh": "[WHISPER]","en": "[WHISPER]"},

    # ── 主题/语言切换 ──
    "toggle.theme":  {"zh": "☀  浅色", "en": "☀  Light"},
    "toggle.lang":   {"zh": "🌐 English", "en": "🌐 中文"},

    # ── 进度/状态消息 ──
    "progress.ffmpeg_init":    {"zh": "正在初始化 FFmpeg...",   "en": "Initializing FFmpeg..."},
    "progress.converting":     {"zh": "正在转换...",            "en": "Converting..."},
    "progress.indeterminate":  {"zh": "正在转换...（无法预估时间）", "en": "Converting... (duration unknown)"},
    "progress.convert_done":   {"zh": "转换完成！",             "en": "Conversion complete!"},
    "progress.loading_model":  {"zh": "正在加载 Whisper 模型",  "en": "Loading Whisper model"},
    "progress.transcribing":   {"zh": "正在转录...（这可能需要较长时间）", "en": "Transcribing... (may take a while)"},
    "progress.saving":         {"zh": "正在保存结果...",        "en": "Saving results..."},
    "progress.transcribe_done":{"zh": "转录完成！",             "en": "Transcription complete!"},
    "progress.pdf_to_image":   {"zh": "正在将 PDF 转换为图片...","en": "Converting PDF to images..."},
    "progress.ocr_page":       {"zh": "正在 OCR 识别第",        "en": "Running OCR on page "},
    "progress.ocr_page_suffix":{"zh": "页...",                 "en": "..."},
    "progress.ocr_done":       {"zh": "OCR 识别完成！共 ",      "en": "OCR complete! "},
    "progress.ocr_pages":      {"zh": " 页",                   "en": " pages"},
    "progress.doc_converting": {"zh": "正在转换文档...",        "en": "Converting document..."},
    "progress.doc_call":       {"zh": "正在调用 Pandoc...",     "en": "Calling Pandoc..."},
    "progress.doc_done":       {"zh": "文档转换完成！",         "en": "Document conversion complete!"},
    "progress.saving_result":  {"zh": "正在保存结果...",        "en": "Saving results..."},
    "log.total_pages":         {"zh": "共 {n} 页需要识别",      "en": "{n} pages to process"},
    "log.lang_detected":       {"zh": "检测到语言: {lang} (概率: {prob:.2%})",
                                 "en": "Detected language: {lang} (probability: {prob:.2%})"},
    "log.device":              {"zh": "使用设备: {device}, 计算类型: {compute}",
                                 "en": "Using device: {device}, compute type: {compute}"},
    "log.cmd":                 {"zh": "执行命令: {cmd}",         "en": "Command: {cmd}"},
    "progress.transcribing_seg":{"zh": "转录中... [{start:.1f}s - {end:.1f}s] {text:.40}...",
                                 "en": "Transcribing... [{start:.1f}s - {end:.1f}s] {text:.40}..."},
    "log.warn_model_size":     {"zh": "{model} 模型约 {size}MB，首次使用将自动下载",
                                 "en": "{model} model ~{size}MB, will auto-download on first use"},
    "log.warn_cancel":         {"zh": "[WARN] 正在取消任务...",  "en": "[WARN] Cancelling task..."},
    "log.selected_file":       {"zh": "[OK] 已选择: {path}",     "en": "[OK] Selected: {path}"},
    "log.convert_start":       {"zh": "{tag} {filename} → {fmt}",
                                 "en": "{tag} {filename} → {fmt}"},
    "log.ocr_start":           {"zh": "[OCR] {filename} → {fmt}  |  lang={lang}",
                                 "en": "[OCR] {filename} → {fmt}  |  lang={lang}"},
    "log.whisper_start":       {"zh": "[WHISPER] {filename} → {fmt}  |  model={model}",
                                 "en": "[WHISPER] {filename} → {fmt}  |  model={model}"},
    "log.success":             {"zh": "[OK] 转换成功 → {path}",   "en": "[OK] Success → {path}"},
    "log.failed":              {"zh": "[ERR] {msg}",              "en": "[ERR] {msg}"},

    # ── 模型对话框 ──
    "model.dialog.title":       {"zh": "Whisper 模型设置",        "en": "Whisper Model Settings"},
    "model.dialog.desc":        {"zh": "选择要使用的模型。模型越大识别越准，但速度越慢、占用空间越大。\nfaster-whisper 会在首次使用时自动缓存模型。",
                                  "en": "Select models to use. Larger models are more accurate but slower.\nfaster-whisper auto-caches models on first use."},
    "model.dialog.download":    {"zh": "⬇  下载选中模型",         "en": "⬇  Download Selected"},
    "model.dialog.close":       {"zh": "关闭",                    "en": "Close"},
    "model.dialog.no_select":   {"zh": "请先选择要下载的模型。",    "en": "Please select models to download."},
    "model.dialog.dl_title":    {"zh": "下载",                    "en": "Download"},
    "model.dialog.dl_msg":      {"zh": "将在首次转录时自动下载以下模型:\n\n", "en": "These models will auto-download on first use:\n\n"},
    "model.dialog.dl_footer":   {"zh": "\n\nfaster-whisper 会缓存模型到本地，无需手动下载。",
                                  "en": "\n\nfaster-whisper caches models locally."},

    # ── 主题切换标签 ──
    "theme.light":  {"zh": "☀  浅色模式",  "en": "☀  Light Mode"},
    "theme.dark":   {"zh": "🌙  深色模式",  "en": "🌙  Dark Mode"},
}


class I18nManager(QObject):
    """管理应用语言"""
    changed = pyqtSignal(str)  # 语言切换信号

    def __init__(self, lang="zh"):
        super().__init__()
        self._lang = lang

    @property
    def lang(self):
        return self._lang

    def set_lang(self, lang: str):
        if lang != self._lang:
            self._lang = lang
            self.changed.emit(lang)

    def t(self, key: str, **kwargs) -> str:
        """获取翻译文本"""
        d = TEXTS.get(key, {})
        text = d.get(self._lang) if d else None
        if text is None:
            # fallback: 尝试中文，再英文，最后返回 key
            text = d.get("zh") or d.get("en") or key
        if kwargs:
            text = text.format(**kwargs)
        return text

    def toggle(self):
        """切换语言"""
        self.set_lang("en" if self._lang == "zh" else "zh")


# 全局实例
i18n = I18nManager()
t = i18n.t  # 快捷方式
