# 自定义主题功能 — 设计文档

- 日期：2026-08-20
- 状态：已获用户批准（方案 A 背景渲染 + 28 项颜色全暴露）
- 关联：UI 样式优化（`2026-08-20-ui-style-design.md`）

## 需求

用户可自定义主题：

1. **自定义颜色**：全部主题颜色键可编辑，每项同时支持「输入十六进制色码」和「色轮选择」（QColorDialog 原生兼具）。
2. **自定义背景**：**窗口区域**与**导航栏**各自独立自定义，每区域可设置：背景颜色（即颜色区的对应色键）、背景图片（jpg/png）、图片透明度。

## 关键决策

- **覆盖叠加模型**：自定义颜色作为覆盖层叠加在基础主题（深 `DARK` / 浅 `LIGHT`）之上；切换深浅时，覆盖颜色仍生效，未覆盖的颜色跟随基础主题。
- **背景渲染 = 方案 A**：自定义绘制背景层（`paintEvent`），等比铺满 + 居中裁切（cover），运行时改透明度零延迟，窗口/导航栏完全独立。
- **全部 28 个颜色键暴露**，含 3 个半透明底色键（`green_bg`/`red_bg`/`drag_glow`）；这些键编辑后按纯 hex 存储（失去原半透明）。

## 数据模型

配置文件：`PROJECT_ROOT/config/user_theme.json`（PROJECT_ROOT 开发=项目根、打包=exe 目录，均在 D 盘）。

```json
{
  "dark": true,
  "colors": { "primary": "#ff5722" },
  "background": {
    "window":  { "image": null, "opacity": 0.5 },
    "sidebar": { "image": null, "opacity": 0.8 }
  }
}
```

- `colors`：仅存被覆盖的色键 → 色值（hex）。
- 生效色 = `{**基础主题, **colors}`。
- JSON 损坏 / 缺失 → 回退默认结构。

## 架构与文件

```
utils/themes.py              # 修改
  - 新增 hex_to_rgba(hex_color, alpha) -> str 助手
  - build_stylesheet(c): QStackedWidget#contentStack 与 QFrame#sidebar 不再设实色背景
    （颜色改由背景层绘制）；其余不变

utils/theme_settings.py      # 新增
  - SETTINGS_PATH = PROJECT_ROOT / "config" / "user_theme.json"
  - DEFAULT_SETTINGS 默认结构（如上）
  - load_settings() -> dict        读取；损坏/缺失回退默认
  - save_settings(s: dict)         原子写（临时文件 + replace）
  - merge_colors(base, overrides)  {**base, **overrides}（仅含合法色键）
  - COLOR_SLOTS: 有序列表 [(key, zh_name), ...]，共 28 项，用于对话框渲染

gui/background.py             # 新增
  - AppBackground(QWidget)        中央部件；paintEvent 填底色(bg_deep) → 有图则
    setOpacity(opacity) + KeepAspectRatioByExpanding 等比铺满居中裁切 → 重置 opacity
  - SidebarBackground(QFrame)     导航栏；绘制底色(bg_sidebar) + 图片 + 1px 右边框
  - 各自 set_background(color_hex, image_path|None, opacity)

gui/theme_settings_dialog.py  # 新增
  - ThemeSettingsDialog(QDialog)
    - 背景区：窗口 / 导航栏 各一行
      图片路径(只读 QLineEdit) + 「选择图片…」(QFileDialog jpg/png) + 「移除」 + 透明度滑块+百分比
    - 颜色区（QScrollArea）：28 行，每行 = 中文名 + 色块按钮(→QColorDialog 色轮+hex) + hex 输入框
      hex↔色块双向同步；非法 hex 红框提示不生效；底部「全部重置」
    - 底部：确定(应用+保存) / 取消
  - result_data() -> dict 返回 {colors, background}

gui/main_window.py            # 修改
  - central → AppBackground；sidebar → SidebarBackground
  - __init__: load_settings() → _theme_is_dark → apply_theme()
  - apply_theme(): 唯一主题应用入口
    base = DARK/LIGHT；colors = merge_colors(base, settings["colors"])；_current_colors = colors
    app.setStyleSheet(build_stylesheet(colors))；palette 同步；_update_theme_widgets(colors)
    bg.set_background(...)；sidebar.set_background(...)；repaint
  - toggle_theme(): 翻转 dark → save_settings → apply_theme
  - open_theme_settings(): 打开对话框 → accept → 合并 → save_settings → apply_theme
  - 新增「主题设置」按钮（objectName toolbarBtn，置于主题/语言切换旁）
  - _update_theme_widgets: page 背景改为透明（背景层负责底色）

main.py                       # 修改
  - 保留启动时 app.setStyleSheet(build_stylesheet(DARK)) 作首帧兜底（避免首帧闪默认风）；
    MainWindow.__init__ 内 apply_theme() 随即以加载的设置覆盖生效
  - 主题应用逻辑收敛进 MainWindow.apply_theme()

tests/                        # 新增（pytest）
  - test_theme_settings.py：存取回环 / 损坏回退 / merge 优先级 / hex_to_rgba
  - test_themes.py：build_stylesheet 含新旧关键色；contentStack/sidebar 不再不透明
  - test_theme_dialog.py（offscreen）：28 行构建 / hex↔色块同步 / 收集覆盖 / 重置
  - test_background.py：背景层构造 + set_background 冒烟
```

## 数据流

1. **启动**：`load_settings()` → MainWindow 依 `dark` 选基础 → `apply_theme()`。
2. **对话框保存**：Accept → 对话框返回 {colors, background} → 合并进 settings → `save_settings()` → `apply_theme()`。
3. **深浅切换**：翻转 `dark` → `save_settings()` → `apply_theme()`（覆盖色保持）。
4. **对话框预览**：对话框内的色块/透明度滑块仅在其内部实时预览（色块即时更新、透明度显示百分比），**不做**主窗口实时预览；点「确定」才写入设置并应用到主窗口（YAGNI）。

## 错误处理

- JSON 损坏 / 缺失 → 回退默认（load_settings 内 try/except）。
- 图片路径无效 / 加载失败（apply 时）→ 日志提示（页面日志区），仅用纯色。
- 用户选到损坏图片 → QMessageBox 提示，不应用。
- 非法 hex 输入 → 红框 + 不更新（保留上次有效值）。

## 测试策略（TDD，先写测试）

- 纯逻辑单测：settings 存取 / merge / hex_to_rgba。
- 样式单测：build_stylesheet 输出断言。
- 对话框 offscreen 测试：构建行数、hex↔色块同步、收集结果、重置。
- 背景层冒烟：构造 + 设置图片/透明度 + 触发重绘不崩溃。

## 验收清单

- [ ] 打开「主题设置」可改任意颜色（hex 与色轮皆可），立即生效并重启后保留
- [ ] 切换深浅主题后自定义覆盖色仍生效
- [ ] 窗口 / 导航栏可各自设置背景图片与透明度，窗口缩放自适应、不拉伸变形
- [ ] 移除背景图后恢复纯色
- [ ] 配置损坏时应用正常启动并回退默认
- [ ] 打包版（dist exe）功能一致
