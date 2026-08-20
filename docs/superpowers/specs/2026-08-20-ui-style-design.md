# Transallum UI 样式优化设计规格

日期：2026-08-20  
范围：**仅修改样式**，业务逻辑与 DOM 结构完全不变  
文件：`utils/themes.py`（主体）、`gui/main_window.py`（日志着色 + 路径 tooltip）

---

## 1. 颜色系统

### 1.1 深色主题（DARK）— 修正项

| Token | 旧值 | 新值 | 原因 |
|---|---|---|---|
| `primary` | `#0ea5e9` | `#1677cb` | 对比度更稳定，与浅色主题统一品牌蓝 |
| `primary_hi` | `#00d4ff` | `#58a6ff` | 深色下更柔和，仍满足 WCAG AA |
| `warning` | 无 | `#faad14` | 新增，日志 `[WARN]` 行着色用 |
| `green` | `#10b981` | `#4ade80` | 深色背景下对比度更高（WCAG AA ✓） |
| `border_focus` | `#00d4ff` | `#58a6ff` | 与 primary_hi 统一 |

`btn_text` 保留 `#0a0e17`（深底按钮深色文字，已为主按钮修正见下文）。

### 1.2 浅色主题（LIGHT）— 修正项

| Token | 旧值 | 新值 | 原因 |
|---|---|---|---|
| `primary` | `#0369a1` | `#1677cb` | 与深色统一品牌蓝 |
| `primary_hi` | `#0284c7` | `#1677cb` | 同上（浅色下悬浮态用 hover 偏移） |
| `warning` | 无 | `#b35c00` | 浅色背景专用，深橙满足 WCAG AA |
| `green` | `#059669` | `#009944` | 对比度更高（报告要求） |
| `bg_sidebar` | `#e8ecf1` | `#e8ecf2` | 微调，与 bg_page `#f0f2f5` 形成明确色阶 |

### 1.3 两套主题共用语义

```
success  → c['green']     （绿）
warning  → c['warning']   （黄/深橙）
error    → c['red']       （红）
info     → c['text_hint'] （灰）
```

---

## 2. 按钮层级

### 2.1 主按钮 `convertBtn`

```css
background-color: c['primary']   /* 实心蓝 */
color: #ffffff                    /* 白字（原为 primary_hi = 蓝字，问题根源）*/
border: none
padding: 12px 44px; font-size: 15px; font-weight: 700; border-radius: 8px
hover → background: darken(primary, 10%)
disabled → opacity: 0.5
```

### 2.2 次要按钮 `browseBtn`（浏览 + 另存为）

```css
background-color: transparent
color: c['primary']              /* 蓝字 */
border: 1.5px solid c['primary']
hover → background: c['drag_glow']（主色淡底）
```

### 2.3 取消按钮 `cancelBtn`

保持不变（红色实心），已满足要求。

---

## 3. 卡片容器

### 3.1 深色模式

- `QGroupBox` 保持 `bg_card: #161b22`，细边框 `border_card: #2c333a`
- 无需改动

### 3.2 浅色模式

- 页面背景 `bg_page: #f0f2f5`（浅灰，作为"画布"）
- 卡片 `QGroupBox bg_card: #ffffff`（白色，浮于页面）
- 边框降权：`border: 1px solid rgba(0,0,0,0.06)`（浅色下边框弱化，靠底色分层）
- 卡片加轻阴影：`box-shadow` 无法直接用 QSS，改为 `border` 颜色微调实现视觉深度

### 3.3 侧边栏

- 浅色：`bg_sidebar: #e8ecf2` vs 页面 `#f0f2f5`，差值明显，无需分割线
- 深色：保持 `#0c0f15`，与页面 `#0d1117` 差值小（深色靠边框）

---

## 4. 日志着色

**实现方式：** 在 `ConverterPage.log()` 方法中，对 `text` 做前缀检测，用 `insertHtml` 替代 `append`，将纯文本日志行包裹在对应颜色的 `<span>` 中。

**规则（按此顺序匹配，取第一个匹配）：**

| 匹配条件 | 颜色 token | 典型内容 |
|---|---|---|
| `[OK]` 开头 或 `✅` | `c['green']` | 成功行 |
| `[WARN]` 或 `⚠` 或 `warning` | `c['warning']` | 警告行 |
| `[ERR]` 或 `❌` 或 `error` | `c['red']` | 错误行 |
| 其他 | `c['text_hint']`（灰）或不着色 | 信息行 |

**关键约束：**
- 调用方（workers）通过 `log` signal 发出的字符串中，已有的 `<span style='color:...'>` HTML 继续保留（不二次处理）
- `log()` 只对**纯文本**行（不含 `<span`）做自动着色
- 日志方法中使用当前激活的颜色字典（`MainWindow._theme_is_dark` 决定 `DARK` 或 `LIGHT`）

---

## 5. 路径输入框 Tooltip

**位置：** `_update_display_for_files()` 和 `on_output_browse()` 中，在设置 `setText()` 的同时，调用 `setToolTip(full_path)`。

**目标控件：**
- `self.file_input`（输入路径）
- `self.output_path`（输出路径）

**实现：**
```python
self.file_input.setText(path)
self.file_input.setToolTip(path)         # ← 新增
self.output_path.setText(str(out_path))
self.output_path.setToolTip(str(out_path))  # ← 新增
```

QSS 中 `QToolTip` 样式已存在（themes.py 末尾），无需额外修改。

---

## 6. 硬编码颜色修复（main_window.py 中的 DARK 引用）

以下代码段目前硬编码 `DARK[...]`，切换到浅色主题后颜色不跟随。

### 修复方案 A（最小改动，推荐）

引入模块级变量 `_current_colors`，初始值为 `DARK`，在 `toggle_theme()` 中更新：

```python
# 模块顶部
_current_colors = DARK

# MainWindow.toggle_theme() 末尾加一行
import gui.main_window as _mw
_mw._current_colors = colors
```

所有 `DARK['green']`、`DARK['red']` 等处改为 `_current_colors['green']` 等。

**涉及位置（全部为视觉代码）：**

| 位置 | 当前 | 改为 |
|---|---|---|
| `_render_status()` L102/107/112 | `DARK["green"]` / `DARK["red"]` / `DARK["text_hint"]` | `_current_colors[...]` |
| `ConverterPage._update_display_for_files()` L321/327 | `DARK['green']` / `DARK['primary_hi']` | `_current_colors[...]` |
| `ConverterPage.on_convert()` L383/389/411/416 | `DARK['green']` / `DARK['red']` / `DARK['primary_hi']` | `_current_colors[...]` |
| `ConverterPage._sep()` L430 | `DARK['text_hint']` | `_current_colors['text_hint']` |
| `DropLineEdit` 内联 QSS L70-73 | `DARK['border_focus']` / `DARK['drag_glow']` / `DARK['primary_hi']` | `_current_colors[...]`（在 retranslate/toggle 时刷新） |
| `MediaPage` trim 标签 inline style L461/472/483 | `DARK['text_hint']` | `_current_colors['text_hint']`（在 retranslate 时刷新） |
| `ConverterPage.setup_ui()` title/fmt/save/status inline style | `DARK[...]` | 移入 `_update_theme_widgets()` 统一管理（已有此方法） |

**`DropLineEdit` 特殊处理：**  
`DropLineEdit` 的拖拽高亮 QSS 用 Python 字符串硬编码，须在 `MainWindow._update_theme_widgets(c)` 中对所有页面的 `file_input` 调用 `setStyleSheet(drag_style(c))`，其中 `drag_style(c)` 是抽取出的辅助函数。

---

## 7. 排版（无需改 DOM，仅 QSS）

| 元素 | 当前 | 目标 | 修改位置 |
|---|---|---|---|
| 页面大标题 | 20pt DemiBold, inline style | 18px 600, `color: primary` | `_update_theme_widgets` 统一 |
| GroupBox 标题 | 13px 600 | 保持 | — |
| 表单标签 (fmt_label, save_label) | 13px, `text_hint` | 13px 400 `text_secondary` | `_update_theme_widgets` |
| 日志文本 | 12px | 12px, line-height 1.5 → QSS 加 `line-height` | themes.py QTextEdit |
| 状态标签 `status_lbl` | 13px `text_hint` | 13px, 按状态着色（done=green，failed=red，其他=hint） | `on_status()` 中动态设置 |

---

## 8. 不在范围内（本次不做）

- 图标替换（线性图标统一 2px 线宽）
- Logo hover 效果
- 空状态占位（`file_input` placeholder 已有，不额外加 SVG）
- Tooltip 为「识别语言」等技术参数添加说明（需改 DOM）
- 模型下载对话框（`WhisperModelDialog`）样式深化

---

## 9. 交付验证清单

- [ ] 浅色侧边栏 `#e8ecf2`，与页面 `#f0f2f5` 色阶明显
- [ ] `convertBtn` 文字 `#ffffff`（白色），与 `browseBtn` 层级清晰
- [ ] 日志纯文本行自动着色（OK=绿，WARN=黄，ERR=红）
- [ ] `file_input` 和 `output_path` 均有 `setToolTip`
- [ ] 切换浅色主题后，日志颜色、状态指示器颜色跟随主题
- [ ] `warning` token 存在于 DARK 和 LIGHT 字典
- [ ] ruff 0 错误（run `ruff check main.py gui utils scripts`）
- [ ] compileall 通过
- [ ] 开发模式启动 GUI 无报错
