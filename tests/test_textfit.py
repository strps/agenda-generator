import subprocess
import sys

import pytest

from agenda.day_extras import truncate
from agenda.textfit import FIT_MODES, CutLog, fit_text, format_ranges


def wo(s):
    return len(s)


def lh(size):
    return size * 0.5


def fit(text, mode, width=10, height=10, size=10.0, **kw):
    return fit_text(text, width, height, size, mode, wo, lh, **kw)


@pytest.mark.parametrize("mode", FIT_MODES)
def test_fitting_text_unchanged(mode):
    r = fit("short", mode)
    assert (r.lines, r.size_pt, r.cut) == (("short",), 10.0, False)


def test_overflow_keeps_long_text():
    t = "a very long title indeed"
    r = fit(t, "overflow")
    assert (r.lines, r.size_pt, r.cut) == ((t,), 10.0, False)


def test_ellipsis_equals_truncate():
    t = "a very long title indeed"
    r = fit(t, "ellipsis")
    assert r.lines == (truncate(t, 10, wo),) and r.cut and r.lines[0].endswith("…")


def test_shrink_without_cut():
    r = fit("x" * 14, "shrink")
    assert not r.cut and r.size_pt < 10 and r.size_pt >= 6
    assert 14 * r.size_pt / 10 <= 10


def test_shrink_cut_below_min_scale():
    r = fit("x" * 30, "shrink")
    assert r.cut and r.size_pt == pytest.approx(6.0) and r.lines[0].endswith("…")
    assert len(r.lines[0]) * 0.6 <= 10


def test_wrap_two_lines():
    r = fit("hello brave world", "wrap", width=12)
    assert r.lines == ("hello brave", "world") and not r.cut and r.size_pt == 10.0


def test_wrap_cut_with_ellipsis():
    r = fit("aaa bbb ccc ddd eee fff", "wrap", width=8)
    assert len(r.lines) == 2 and r.cut and r.lines[-1].endswith("…")


def test_wrap_breaks_long_word():
    r = fit("abcdefghijklmnopqrst", "wrap", width=10)
    assert r.lines == ("abcdefghij", "klmnopqrst") and not r.cut


def test_wrap_reduces_size_for_height():
    r = fit("hello brave world", "wrap", width=8, height=6.5)
    assert len(r.lines) == 2 and r.size_pt < 10 and not r.cut


def test_cutlog():
    log = CutLog()
    assert not log
    for p, reg in [(5, "header"), (3, "footer"), (4, "footer"), (1, "footer"), (5, "footer")]:
        log.add(p, reg, f"t{p}")
    assert log
    assert [e.page for e in log.entries] == [1, 3, 4, 5, 5]
    assert log.pages() == [1, 3, 4, 5]
    assert log.pages("footer") == [1, 3, 4, 5]
    assert log.pages("header") == [5]
    assert format_ranges(log.pages("footer")) == "1, 3-5"


def test_format_ranges():
    assert format_ranges([14, 15, 16, 17, 18, 19, 20, 3, 5]) == "3, 5, 14-20"
    assert format_ranges([]) == ""


def test_module_is_qt_and_fpdf_free():
    code = "import agenda.textfit, sys; assert 'PySide6' not in sys.modules and 'fpdf' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)
