import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect  # noqa: E402

from agenda.gui import layout as L  # noqa: E402
from agenda.gui import template_model as TM  # noqa: E402
from agenda.gui.app import MainWindow  # noqa: E402
from agenda.gui.preview import PreviewWidget  # noqa: E402
from agenda.templates import GLOBAL, STYLING, TEMPLATE_KEYS  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def win(qapp):
    w = MainWindow()
    yield w
    for pv in [w.preview, *w.template_previews.values()]:
        pv.wait_idle()


def _current(win):
    return win.preview_stack.currentWidget().objectName()


def test_structure(win):
    assert win.preview_stack.count() == 1 + len(TEMPLATE_KEYS)
    assert win.preview_stack.widget(0) is win.preview
    assert win.regions[L.PREVIEW] is win.preview
    assert win.preview_key == GLOBAL


def test_follows_active_section(win):
    win.settings.activate("daily")
    assert _current(win) == "template_page_daily"
    pv = win.template_previews["daily"]
    pv.wait_idle()
    cfg, _ = win.settings.config()
    assert len(pv.plan) == len(TM.sample_plan(cfg, "daily"))
    assert not pv.busy
    win.settings.notify_focus(win.settings.editors["qr_urls"])
    assert _current(win) == "template_page_qr"


def test_styling_and_global(win):
    win.settings.activate(STYLING)
    assert win.preview_stack.currentIndex() == 0
    win.settings.activate("daily")
    win.settings.activate(STYLING)
    assert _current(win) == "template_page_daily"
    win.settings.activate(GLOBAL)
    assert win.preview_stack.currentIndex() == 0
    assert win.preview_key == GLOBAL


def test_weekly_spread(win):
    assert win.template_previews["weekly"].mode == "spread"


def test_inactive_and_notice(win):
    qr = win.template_previews["qr"]
    assert qr.inactive
    assert win.template_notices["qr"].text()
    assert isinstance(qr.scroll.graphicsEffect(), QGraphicsOpacityEffect)
    win.settings.editors["qr_urls"].setPlainText("https://example.com")
    win.settings.sections["qr"].enable_box.click()
    win.flush_preview()
    assert not qr.inactive
    assert qr.scroll.graphicsEffect() is None
    assert win.template_notices["qr"].text() == ""
    win.settings.sections["daily"].enable_box.click()
    win.flush_preview()
    assert win.template_previews["daily"].inactive


def test_only_visible_template_updates(win, monkeypatch):
    win.settings.activate("daily")
    calls = []
    for key, pv in [(GLOBAL, win.preview), *win.template_previews.items()]:
        orig = pv.set_plan
        monkeypatch.setattr(
            pv, "set_plan", lambda c, p, orig=orig, key=key: (calls.append(key), orig(c, p))[1]
        )
    win.settings.editors["year"].setValue(2031)
    win.flush_preview()
    assert sorted(calls) == sorted([GLOBAL, "daily"])


def test_invalid_config(win):
    win.settings.set_values({**win.settings.values(), "imposition": True, "booklet_folded": False})
    win.flush_preview()
    assert win.settings.config()[0] is None
    assert all(pv.plan is None for pv in win.template_previews.values())


def test_page_requested_shows_full(win):
    win.settings.activate("daily")
    win.section_bar.page_requested.emit(0)
    assert win.preview_stack.currentIndex() == 0
    assert win.preview_key == GLOBAL


def test_set_inactive_survives_refresh(qapp):
    pv = PreviewWidget()
    pv.set_inactive(True)
    pv.refresh()
    assert isinstance(pv.scroll.graphicsEffect(), QGraphicsOpacityEffect)
