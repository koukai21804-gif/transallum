from utils.color_utils import alpha_of, make_color, normalize_color, split_color


def test_split_hex6():
    assert split_color("#ff5722") == (255, 87, 34, 1.0)
    assert split_color("ff5722") == (255, 87, 34, 1.0)


def test_split_hex3():
    assert split_color("#f52") == (255, 85, 34, 1.0)


def test_split_rgb_rgba():
    assert split_color("rgb(255, 87, 34)") == (255, 87, 34, 1.0)
    assert split_color("rgba(74, 222, 128, 0.08)") == (74, 222, 128, 0.08)
    assert split_color("RGBA(255, 255, 255, 0.5)") == (255, 255, 255, 0.5)


def test_split_invalid():
    assert split_color("") is None
    assert split_color("#12345") is None
    assert split_color("#ggg000") is None
    assert split_color("notacolor") is None


def test_make_opaque_hex():
    assert make_color(255, 87, 34, 1.0) == "#FF5722"
    assert make_color(255, 87, 34, 0.999) == "#FF5722"   # 近似不透明归为 hex


def test_make_translucent_rgba():
    assert make_color(74, 222, 128, 0.08) == "rgba(74, 222, 128, 0.08)"
    assert make_color(255, 87, 34, 0.5) == "rgba(255, 87, 34, 0.5)"
    assert make_color(255, 87, 34, 0) == "rgba(255, 87, 34, 0)"


def test_alpha_of():
    assert alpha_of("#ff5722") == 1.0
    assert alpha_of("rgba(74, 222, 128, 0.08)") == 0.08
    assert alpha_of("garbage") == 1.0


def test_normalize_roundtrip():
    assert normalize_color("#ff5722") == "#FF5722"
    assert normalize_color("#F5722") is None
    assert normalize_color("rgba(74, 222, 128, 0.08)") == "rgba(74, 222, 128, 0.08)"
