"""深色/浅色主题定义"""

# ── 深色主题色彩 ──
DARK = {
    "bg_deep":      "#0a0e17",
    "bg_card":      "#111827",
    "bg_log":       "#0c0f15",
    "bg_input":     "#1a1f2e",
    "bg_sidebar":   "#0c0f15",
    "bg_tools":     "#0f131a",
    "border_card":  "#334155",
    "border_ctrl":  "#1e293b",
    "border_focus": "#00d4ff",
    "primary":      "#0ea5e9",
    "primary_hi":   "#00d4ff",
    "btn_text":     "#0a0e17",    # 深底按钮用深色文字
    "text_title":   "#e6edf3",
    "text_body":    "#c9d1d9",
    "text_hint":    "#64748b",
    "text_dim":     "#475569",
    "green":        "#10b981",
    "red":          "#ef4444",
    "green_bg":     "rgba(16,185,129,0.08)",
    "red_bg":       "rgba(239,68,68,0.08)",
    "scrollbar":    "#334155",
    "scroll_hover": "#0ea5e9",
    "drag_glow":    "rgba(0,212,255,0.06)",
}

# ── 浅色主题色彩 ──
LIGHT = {
    "bg_deep":      "#f0f2f5",
    "bg_card":      "#ffffff",
    "bg_log":       "#f8f9fa",
    "bg_input":     "#ffffff",
    "bg_sidebar":   "#e8ecf1",
    "bg_tools":     "#f8f9fa",
    "border_card":  "#d1d5db",
    "border_ctrl":  "#d1d5db",
    "border_focus": "#0284c7",
    "primary":      "#0369a1",    # 深蓝，白字高对比
    "primary_hi":   "#0284c7",    # 亮蓝
    "btn_text":     "#ffffff",    # 按钮文字始终白色
    "text_title":   "#1e293b",
    "text_body":    "#334155",
    "text_hint":    "#94a3b8",
    "text_dim":     "#cbd5e1",
    "green":        "#059669",
    "red":          "#dc2626",
    "green_bg":     "rgba(5,150,105,0.06)",
    "red_bg":       "rgba(220,38,38,0.06)",
    "scrollbar":    "#cbd5e1",
    "scroll_hover": "#0369a1",
    "drag_glow":    "rgba(3,105,161,0.10)",
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

/* 主内容区背景 */
QStackedWidget#contentStack {{
    background-color: {c['bg_deep']};
}}

QWidget {{
    color: {c['text_body']};
    font-family: "Microsoft YaHei", "Segoe UI", "Noto Sans SC", sans-serif;
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
    color: {c['primary_hi']};
    background-color: {c['bg_card']};
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

/* 主按钮 — 与次级按钮同蓝色系，实心填充 */
QPushButton#convertBtn {{
    background-color: {c['primary']};
    color: {c['primary_hi']};
    border: 1px solid {c['primary_hi']};
    padding: 12px 44px;
    font-size: 15px;
    font-weight: 700;
    border-radius: 8px;
}}
QPushButton#convertBtn:hover {{
    background-color: {c['primary_hi']};
    color: #ffffff;
    border-color: {c['primary_hi']};
}}
QPushButton#convertBtn:disabled {{
    background-color: {c['primary']};
    color: {c['primary_hi']};
    border: 1px solid {c['primary_hi']};
}}

/* 次级按钮 */
QPushButton#browseBtn {{
    background-color: transparent;
    color: {c['primary_hi']};
    border: 1px solid {c['primary']};
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
}}
QPushButton#browseBtn:hover {{
    background-color: {c['drag_glow']};
    border-color: {c['primary_hi']};
}}

/* 取消按钮 */
QPushButton#cancelBtn {{
    background-color: {c['red']};
    color: #f1f5f9;
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
QFrame#sidebar {{
    background-color: {c['bg_sidebar']};
    border-right: 1px solid {c['border_ctrl']};
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
    border: 1px solid {c['border_ctrl']};
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
