"""render_pages: partial rendering shares the full-export path."""

from __future__ import annotations

import io

import pytest
from helpers import drawn_points
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.config import Config
from agenda.exporter import export_agenda, render_pages


@pytest.fixture(scope="module")
def cfg():
    return Config(year=2026, planners=["weekly"], daily_months=[])


@pytest.fixture(scope="module")
def plan(cfg):
    return build_plan(cfg)


def _streams(data: bytes) -> list[tuple]:
    """Per page: text and drawn geometry (glyph ids/font names differ between subsets)."""
    texts = [p.extract_text() for p in PdfReader(io.BytesIO(data)).pages]
    return list(zip(texts, drawn_points(data), strict=True))


def test_all_pages_match_full_export(cfg, plan, tmp_path):
    path = export_agenda(cfg, tmp_path / "full.pdf")
    full = _streams(path.read_bytes())
    assert _streams(render_pages(cfg, plan, range(len(plan)))) == full


def test_subset_matches_same_pages_of_full(cfg, plan, tmp_path):
    full = _streams(export_agenda(cfg, tmp_path / "full.pdf").read_bytes())
    idx = [0, 5, 6, len(plan) - 1]
    assert _streams(render_pages(cfg, plan, idx)) == [full[i] for i in idx]


def test_only_requested_count_and_order_dedupe(cfg, plan):
    data = render_pages(cfg, plan, [7, 3, 3])
    assert len(PdfReader(io.BytesIO(data)).pages) == 2
    assert _streams(data) == _streams(render_pages(cfg, plan, [3, 7]))


def test_left_right_sides_use_real_page_number(cfg, plan, tmp_path):
    full = _streams(export_agenda(cfg, tmp_path / "full.pdf").read_bytes())
    # Same page content needs same margins: pick one odd and one even page.
    for i in (10, 11):
        assert _streams(render_pages(cfg, plan, [i])) == [full[i]]


def test_partial_spread_instance(cfg, plan, tmp_path):
    spread = next(i for i, e in enumerate(plan) if e.page_in_instance == 1)
    full = _streams(export_agenda(cfg, tmp_path / "full.pdf").read_bytes())
    for i in (spread, spread - 1):
        assert _streams(render_pages(cfg, plan, [i])) == [full[i]]


def test_empty_and_out_of_range(cfg, plan):
    with pytest.raises(ValueError):
        render_pages(cfg, plan, [])
    with pytest.raises(IndexError):
        render_pages(cfg, plan, [len(plan)])
    with pytest.raises(IndexError):
        render_pages(cfg, plan, [-1])
