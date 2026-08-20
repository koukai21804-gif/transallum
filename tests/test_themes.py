from utils.themes import DARK, build_stylesheet


def _segment(sheet: str, marker: str) -> str:
    i = sheet.find(marker)
    assert i >= 0, f"QSS 中找不到 {marker}"
    return sheet[i:i + 300]


def test_stylesheet_has_new_primary():
    assert "#1677cb" in build_stylesheet(DARK)


def test_content_stack_transparent():
    seg = _segment(build_stylesheet(DARK), "contentStack")
    assert "background-color: transparent" in seg


def test_sidebar_transparent():
    # 块隔离断言：只检查 #sidebar 自身规则块，避免 300 字符片段
    # 溢入紧随其后的 QPushButton#navBtn 的 transparent 规则造成误判
    sheet = build_stylesheet(DARK)
    i = sheet.find("#sidebar")
    assert i >= 0, "QSS 中找不到 #sidebar"
    end = sheet.index("}", i)
    block = sheet[i:end]
    assert "background-color: transparent" in block
