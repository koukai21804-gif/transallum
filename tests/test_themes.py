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
    seg = _segment(build_stylesheet(DARK), "#sidebar")
    assert "background-color: transparent" in seg
