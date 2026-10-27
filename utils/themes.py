"""深色/浅色主题定义"""

# ── 深色主题色彩 ──
DARK = {
    "font_family":  "Microsoft YaHei",
    "bg_deep":      "#0a0e17",
    "bg_card":      "#111827",
    "chip_bg":      "#1d2837",
    "bg_log":       "#0c0f15",
    "bg_input":     "#1a1f2e",
    "bg_sidebar":   "#0c0f15",
    "bg_tools":     "#0f131a",
    "border_card":  "#334155",
    "border_ctrl":  "#1e293b",
    "border_focus": "#58a6ff",
    "primary":      "#1677cb",
    "primary_hi":   "#58a6ff",
    "page_title":   "#e6edf3",   # 页面大标题 / brand 名独立颜色（与主色高亮解耦）
    "btn_text":     "#0a0e17",    # 深底按钮用深色文字
    "text_title":   "#e6edf3",
    "text_body":    "#c9d1d9",
    "text_hint":    "#64748b",
    "text_dim":     "#475569",
    "green":        "#4ade80",
    "red":          "#ef4444",
    "warning":      "#faad14",
    "green_bg":     "rgba(74,222,128,0.08)",
    "red_bg":       "rgba(239,68,68,0.08)",
    "scrollbar":    "#334155",
    "scroll_hover": "#58a6ff",
    "drag_glow":    "rgba(22,119,203,0.08)",
}

# ── 浅色主题色彩（底色分层：画布 → 侧栏 → 白色卡片，输入/日志为内凹井，描边退后） ──
LIGHT = {
    "font_family":  "Microsoft YaHei UI",
    "bg_deep":      "#e9ecf2",
    "bg_card":      "#ffffff",
    "chip_bg":      "#e9f0f9",
    "bg_log":       "#eef1f6",
    "bg_input":     "#f2f5f9",
    "bg_sidebar":   "#dfe4ec",
    "bg_tools":     "#ffffff",
    "border_card":  "#d3dae2",
    "border_ctrl":  "#dde2ea",
    "border_focus": "#1677cb",
    "primary":      "#1677cb",    # 统一品牌蓝
    "primary_hi":   "#1677cb",    # 浅色下主色即高亮色
    "page_title":   "#1e293b",   # 页面大标题 / brand 名独立颜色（与主色高亮解耦）
    "btn_text":     "#ffffff",    # 按钮文字始终白色
    "text_title":   "#1e293b",
    "text_body":    "#334155",
    "text_hint":    "#5a6677",
    "text_dim":     "#cbd5e1",
    "green":        "#00753a",
    "red":          "#c02828",
    "warning":      "#a14f00",
    "green_bg":     "rgba(0,153,68,0.08)",
    "red_bg":       "rgba(220,38,38,0.06)",
    "scrollbar":    "#cbd5e1",
    "scroll_hover": "#1677cb",
    "drag_glow":    "rgba(22,119,203,0.10)",
}


def build_stylesheet(c: dict) -> str:
    """根据色彩字典生成完整 QSS 样式表"""
    return f"""
/* ================================================================
   GLOBAL
   ================================================================ */
QMainWindow {{
    background-color: {c['bg_deep']};
}}

/* 主内容区背景（实际底色由 AppBackground 背景层绘制） */
QStackedWidget#contentStack {{
    background-color: transparent;
}}
QStackedWidget#contentStack > QWidget {{
    background-color: transparent;
}}

QWidget {{
    color: {c['text_body']};
    font-family: "{c['font_family']}";
}}

/* ================================================================
   GROUPBOX — 卡片面板
   ================================================================ */
QGroupBox {{
    font-weight: 600;
    font-size: 13px;
    color: {c['text_title']};
    border: 1px solid {c['border_card']};
    border-radius: 8px;
    margin-top: 14px;
    padding: 18px 16px 14px 16px;
    background-color: {c['bg_card']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 10px;
    color: {c['text_title']};
    background-color: {c['chip_bg']};
    border-radius: 4px;
}}

/* ================================================================
   PUSHBUTTON
   ================================================================ */
QPushButton {{
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 13px;
    color: {c['text_body']};
    background-color: {c['border_ctrl']};
    border: 1px solid {c['border_card']};
}}
QPushButton:hover {{
    border-color: {c['border_focus']};
    color: {c['text_title']};
}}

/* 主按钮 — 实心蓝底白字（无外描边） */
QPushButton#convertBtn {{
    background-color: {c['primary']};
    color: {c['btn_text']};
    border: none;
    padding: 12px 44px;
    font-size: 15px;
    font-weight: 700;
    border-radius: 8px;
}}
QPushButton#convertBtn:hover {{
    background-color: {c['primary_hi']};
    color: {c['btn_text']};
    border: none;
}}
QPushButton#convertBtn:disabled {{
    background-color: {c['primary']};
    color: {c['btn_text']};
    border: none;
}}

/* 次级按钮 */
QPushButton#browseBtn {{
    background-color: transparent;
    color: {c['primary']};
    border: 1.5px solid {c['primary']};
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
}}
QPushButton#browseBtn:hover {{
    background-color: {c['drag_glow']};
    border-color: {c['primary_hi']};
    color: {c['primary_hi']};
}}

/* 取消按钮 */
QPushButton#cancelBtn {{
    background-color: {c['red']};
    color: {c['btn_text']};
    border: none;
    padding: 12px 34px;
    font-size: 15px;
    font-weight: 700;
    border-radius: 8px;
}}
QPushButton#cancelBtn:hover {{
    background-color: #f04444;
}}

/* ================================================================
   QLINEEDIT / QCOMBOBOX
   ================================================================ */
QLineEdit {{
    border: 1px solid {c['border_ctrl']};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    background-color: {c['bg_input']};
    color: {c['text_title']};
    selection-background-color: {c['primary']};
    selection-color: #ffffff;
}}
QLineEdit:focus {{
    border-color: {c['border_focus']};
}}
QLineEdit:disabled {{
    background-color: {c['bg_deep']};
    color: {c['text_dim']};
}}
QLineEdit:read-only {{
    color: {c['text_hint']};
}}

QComboBox {{
    border: 1px solid {c['border_ctrl']};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    background-color: {c['bg_input']};
    color: {c['text_title']};
    min-width: 120px;
}}
QComboBox:hover {{
    border-color: {c['primary']};
}}
QComboBox:focus {{
    border-color: {c['border_focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
    subcontrol-position: right center;
    subcontrol-origin: padding;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {c['bg_card']};
    color: {c['text_body']};
    border: 1px solid {c['border_card']};
    border-radius: 8px;
    selection-background-color: {c['primary']};
    selection-color: #ffffff;
    padding: 6px;
    outline: none;
    margin-top: 2px;
}}
QComboBox:disabled {{
    background-color: {c['bg_deep']};
    color: {c['text_dim']};
}}

/* ================================================================
   QPROGRESSBAR
   ================================================================ */
QProgressBar {{
    border: none;
    border-radius: 8px;
    background-color: {c['bg_input']};
    text-align: center;
    font-weight: 700;
    font-size: 12px;
    color: {c['text_body']};
    height: 26px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['primary']}, stop:0.5 #00c8f0, stop:1 {c['primary_hi']});
    border-radius: 8px;
}}

/* ================================================================
   QTEXTEDIT — 日志终端
   ================================================================ */
QTextEdit {{
    border: 1px solid {c['border_card']};
    border-radius: 8px;
    background-color: {c['bg_log']};
    color: {c['text_body']};
    font-family: "Cascadia Code", "JetBrains Mono", "Fira Code",
                 "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 10px 12px;
    selection-background-color: {c['primary']};
    selection-color: #ffffff;
}}

/* ================================================================
   SIDEBAR
   ================================================================ */
#sidebar {{
    background-color: transparent;
}}
QPushButton#navBtn {{
    background-color: transparent;
    color: {c['text_hint']};
    border: none;
    border-radius: 8px;
    padding: 13px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#navBtn:hover {{
    background-color: {c['drag_glow']};
    color: {c['text_body']};
}}
QPushButton#navBtn:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['primary']}, stop:1 {c['primary_hi']});
    color: #ffffff;
    font-weight: 700;
}}

/* ================================================================
   顶部工具栏按钮 (主题/语言切换)
   ================================================================ */
QPushButton#toolbarBtn {{
    background-color: transparent;
    color: {c['text_hint']};
    border: 1px solid {c['border_ctrl']};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#toolbarBtn:hover {{
    background-color: {c['drag_glow']};
    color: {c['text_title']};
    border-color: {c['primary_hi']};
}}

/* ================================================================
   SCROLLBAR
   ================================================================ */
QScrollBar:vertical {{
    background-color: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background-color: {c['scrollbar']};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {c['scroll_hover']};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}
QScrollBar:horizontal {{
    background-color: transparent;
    height: 6px;
    border-radius: 3px;
    margin: 2px 4px;
}}
QScrollBar::handle:horizontal {{
    background-color: {c['scrollbar']};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {c['scroll_hover']};
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ================================================================
   SPECIAL
   ================================================================ */
QLabel {{
    background-color: transparent;
    color: {c['text_body']};
}}
QFrame#sepLine {{
    background-color: {c['border_ctrl']};
    max-height: 1px;
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QFrame#toolsCard {{
    background-color: {c['bg_tools']};
    border: 1px solid {c['border_card']};
    border-radius: 8px;
}}
QFrame#toolsCard QLabel {{
    background: transparent;
}}
QFrame#topBar {{
    background-color: {c['bg_sidebar']};
    border-bottom: 1px solid {c['border_ctrl']};
}}
QFrame#topBar QLabel {{
    background: transparent;
}}

/* ================================================================
   DIALOG / MESSAGEBOX
   ================================================================ */
QDialog {{
    background-color: {c['bg_card']};
    color: {c['text_body']};
}}
QMessageBox {{
    background-color: {c['bg_card']};
}}
QMessageBox QLabel {{
    color: {c['text_body']};
    background: transparent;
}}
QMessageBox QPushButton {{
    background-color: {c['border_ctrl']};
    color: {c['text_body']};
    border: 1px solid {c['border_card']};
    border-radius: 8px;
    padding: 8px 24px;
    font-weight: 600;
}}
QMessageBox QPushButton:hover {{
    background-color: {c['primary']};
    color: #ffffff;
    border-color: {c['primary']};
}}
QCheckBox {{
    color: {c['text_body']};
    spacing: 10px;
    font-size: 13px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 19px;
    height: 19px;
    border: 2px solid {c['border_card']};
    border-radius: 5px;
    background-color: {c['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {c['primary']};
    border-color: {c['primary_hi']};
}}
QCheckBox::indicator:hover {{
    border-color: {c['primary_hi']};
}}
QToolTip {{
    background-color: {c['bg_card']};
    color: {c['text_title']};
    border: 1px solid {c['primary_hi']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""
