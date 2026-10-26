import os

import pytest

from agenda.gui import preview_model as M


def test_spread_pairs_even_page_with_next_odd_page():
    assert M.spread_indices(0, 10) == [0]  # page 1 stands alone
    assert M.spread_indices(1, 10) == [1, 2]
    assert M.spread_indices(2, 10) == [1, 2]
    assert M.spread_indices(9, 10) == [9]  # last even page alone
    assert M.spread_indices(8, 10) == [7, 8]


def test_sheet_rows_saddle_stitch():
    booklet = [1] * 8 + [2] * 8
    assert M.sheet_rows(0, booklet) == [[7, 0], [1, 6]]
    assert M.sheet_rows(6, booklet) == [[7, 0], [1, 6]]
    assert M.sheet_rows(3, booklet) == [[5, 2], [3, 4]]
    assert M.sheet_rows(8, booklet) == [[15, 8], [9, 14]]


def test_sheet_rows_partial_sheet_leaves_missing_pages_out():
    booklet = [1, 1, 1]  # e.g. a template sample: filler + two-page week
    assert M.sheet_rows(0, booklet) == [[0], [1, 2]]
    assert M.sheet_rows(2, booklet) == [[0], [1, 2]]
    assert M.sheet_number(1, booklet) == 1


def test_sheet_rows_cover_outside_booklets_is_a_spread():
    booklet = [None, None, 1, 1, 1, 1, None, None]
    assert M.sheet_rows(0, booklet) == [[0]]
    assert sorted(i for r in M.sheet_rows(3, booklet) for i in r) == [2, 3, 4, 5]


def test_every_page_in_exactly_one_sheet():
    booklet = [1] * 12
    seen = {}
    for i in range(12):
        seen.setdefault(tuple(map(tuple, M.sheet_rows(i, booklet))), set()).add(i)
    assert sorted(len(v) for v in seen.values()) == [4, 4, 4]


def test_display_rows_by_mode_and_sheet_fallback():
    b = [1] * 8
    assert M.display_rows(M.SINGLE, 3, 8, b, True) == [[3]]
    assert M.display_rows(M.SPREAD, 3, 8, b, True) == [[3, 4]]
    assert M.display_rows(M.SHEET, 3, 8, b, True) == [[5, 2], [3, 4]]
    assert M.display_rows(M.SHEET, 3, 8, b, False) == [[3, 4]]
    with pytest.raises(ValueError):
        M.effective_mode("bogus", True)


def test_render_indices_and_pdf_position_follow_plan_order():
    rows = [[5, 2], [3, 4]]
    assert M.render_indices(rows) == [2, 3, 4, 5]
    assert M.pdf_position(rows, 5) == 3 and M.pdf_position(rows, 2) == 0


def test_step_clamps_and_moves_by_unit():
    b = [1] * 8
    assert M.step(M.SINGLE, 0, -1, 8, b, True) == 0
    assert M.step(M.SINGLE, 3, 2, 8, b, True) == 5
    assert M.step(M.SPREAD, 0, 1, 8, b, True) == 1
    assert M.step(M.SPREAD, 1, 1, 8, b, True) == 3
    assert M.step(M.SPREAD, 3, -1, 8, b, True) == 2
    assert M.step(M.SPREAD, 7, 1, 8, b, True) == 7
    b2 = [1] * 8 + [2] * 8
    assert M.step(M.SHEET, 0, 1, 16, b2, True) == 2
    assert M.step(M.SHEET, 1, 1, 16, b2, True) == 2
    assert M.step(M.SHEET, 6, 1, 16, b2, True) == 2
    assert M.step(M.SHEET, 5, 1, 16, b2, True) == 8
    assert M.step(M.SHEET, 8, -1, 16, b2, True) == 2
    assert M.step(M.SHEET, 8, 5, 16, b2, True) == 10


def test_zoom_scale_fixed_and_fit():
    assert M.zoom_scale(100, (100, 200), 1, 1, (500, 500)) == pytest.approx(96 / 72)
    assert M.zoom_scale(50, (100, 200), 1, 1, (500, 500)) == pytest.approx(96 / 72 / 2)
    # fit: two pages wide, limited by width
    assert M.zoom_scale(M.FIT, (100, 100), 1, 2, (408, 1000)) == pytest.approx(2.0)
    # limited by height
    assert M.zoom_scale(M.FIT, (100, 100), 1, 1, (1000, 300)) == pytest.approx(3.0)
    assert M.zoom_scale(M.FIT, (100, 100), 1, 1, (0, 0)) > 0
    with pytest.raises(ValueError):
        M.zoom_scale(33, (1, 1), 1, 1, (1, 1))


def test_label():
    assert M.label([[71, 72]], 498, M.SPREAD) == "Spread 72-73 of 498"
    assert M.label([[0]], 498, M.SINGLE) == "Page 1 of 498"
    assert M.label([[5, 2], [3, 4]], 16, M.SHEET) == "Sheet 3,4,5,6 of 16"


@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    pytest.importorskip("pypdfium2")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _widget():
    from agenda.assembler import build_plan
    from agenda.config import Config
    from agenda.gui.preview import PreviewWidget

    cfg = Config()
    w = PreviewWidget()
    w.resize(900, 700)
    w.set_plan(cfg, build_plan(cfg))
    assert w.wait_idle()
    return w


def _shown(w):
    return [w.grid.itemAt(i).widget() for i in range(w.grid.count())]


def test_widget_modes_show_expected_page_counts(qapp):
    w = _widget()
    w.goto(10)
    assert w.wait_idle()
    assert len(_shown(w)) == 2 and w.label.text().startswith("Spread")
    pix = _shown(w)[0].pixmap()
    assert not pix.isNull() and pix.width() > 50
    w.set_mode(M.SINGLE)
    assert w.wait_idle()
    assert len(_shown(w)) == 1
    w.set_mode(M.SHEET)
    assert w.wait_idle()
    assert len(_shown(w)) == 2  # front and back, each side one picture
    side = _shown(w)[0].pixmap()
    assert side.width() > side.height()  # two portrait pages joined
    w.move(1)
    assert w.wait_idle()
    assert w.index != 10


def test_widget_zoom_changes_pixmap_size_and_error_message(qapp):
    w = _widget()
    w.set_mode(M.SINGLE)
    assert w.wait_idle()
    w.set_zoom(50)
    assert w.wait_idle()
    small = _shown(w)[0].pixmap().width()
    w.set_zoom(200)
    assert w.wait_idle()
    assert _shown(w)[0].pixmap().width() == pytest.approx(small * 4, abs=4)
    w.set_error("bad year")
    assert w.message.text() == "bad year" and not _shown(w)


def test_main_window_preview_follows_settings(qapp):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    assert win.preview.plan is not None
    win.settings.set_values({**win.settings.values(), "year": 2031})
    win.flush_preview()
    assert win.preview.wait_idle()
    assert win.preview.cfg.year == 2031


def test_config_hash_and_cache_key():
    from agenda.config import Config
    from agenda.gui.render_cache import cache_key, config_hash

    a, b = Config(), Config(year=2031)
    assert config_hash(a) == config_hash(Config())
    assert config_hash(a) != config_hash(b)
    assert cache_key("h", 3, 100) != cache_key("h", 3, 50)


def test_lru_cache_evicts_least_recently_used():
    from agenda.gui.render_cache import LruCache

    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1  # a is now most recent
    c.put("c", 3)
    assert "b" not in c and "a" in c and "c" in c and len(c) == 2
    assert c.get("zzz") is None
    c.clear()
    assert len(c) == 0
    with pytest.raises(ValueError):
        LruCache(0)


def test_debounce_waits_for_quiet_period_and_keeps_latest():
    from agenda.gui.render_cache import Debounce

    t = [0.0]
    d = Debounce(0.3, clock=lambda: t[0])
    assert d.take() == (False, None)
    d.push("a")
    t[0] = 0.2
    d.push("b")  # restarts the wait
    t[0] = 0.4
    assert d.take() == (False, None)
    t[0] = 0.5
    assert d.take() == (True, "b")
    assert d.take() == (False, None) and not d.pending
    d.push("c")
    assert d.flush() == (True, "c")


def test_latest_gate_drops_outdated_results():
    from agenda.gui.render_cache import LatestGate

    g = LatestGate()
    first, second = g.issue(), g.issue()
    assert not g.is_current(first) and g.is_current(second)


def test_widget_caches_images_and_navigation_reuses_them(qapp):
    w = _widget()
    w.set_mode(M.SINGLE)
    w.set_zoom(50)
    assert w.wait_idle()
    w.goto(5)
    assert w.wait_idle()
    n = len(w.cache)
    w.goto(6)
    w.goto(5)  # back: fully cached, no render
    assert not w.busy and len(w.cache) >= n


def test_widget_drops_stale_result(qapp):
    w = _widget()
    w.set_mode(M.SINGLE)
    w.set_zoom(50)
    assert w.wait_idle()
    w.goto(20)  # request queued...
    w.goto(30)  # ...and superseded before it is delivered
    assert w.wait_idle()
    assert w.rows() == [[30]]
    assert len(_shown(w)) == 1


def test_main_window_debounces_settings_changes(qapp):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    assert win.preview.wait_idle()
    for year in (2030, 2031, 2032):
        win.settings.set_values({**win.settings.values(), "year": year})
    assert win.debounce.pending and win.preview.cfg.year != 2032
    win.flush_preview()
    assert not win.debounce.pending and win.preview.cfg.year == 2032
    assert win.preview.wait_idle()
