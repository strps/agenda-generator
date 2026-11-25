"""Cut report text (Qt-free), English and Spanish."""

from __future__ import annotations

import pytest

from agenda.cutreport import cut_report_lines, cut_status
from agenda.textfit import CutLog
from agenda.uitext import get_language, set_language


@pytest.fixture(autouse=True)
def _restore_language():
    old = get_language()
    yield
    set_language(old)


def _log():
    log = CutLog()
    for p in (5, 9, *range(14, 21)):
        log.add(p, "header", "A very long title")
    log.add(3, "footer", "x" * 80)
    return log


def test_english_lines():
    set_language("en")
    lines = cut_report_lines(_log())
    assert lines[0] == "Header text was shortened on 9 agenda pages: 5, 9, 14-20"
    assert lines[1] == '  "A very long title" (agenda pages 5, 9, 14-20)'
    assert lines[2] == "Footer text was shortened on 1 agenda page: 3"
    assert lines[3] == f'  "{"x" * 59}…" (agenda page 3)'
    assert cut_status(_log()) == "⚠ 10 pages with shortened text"


def test_spanish_lines():
    set_language("es")
    lines = cut_report_lines(_log())
    assert "5, 9, 14-20" in lines[0] and "encabezado" in lines[0]
    assert "pie" in lines[2] and "página" in lines[2]


def test_empty_log():
    assert cut_report_lines(CutLog()) == [] and cut_status(CutLog()) == ""
