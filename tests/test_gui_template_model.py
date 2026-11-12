import io
from pathlib import Path

import pytest
from pypdf import PdfReader

from agenda.assembler import PagePlan
from agenda.catalog import get_page
from agenda.config import Config
from agenda.exporter import render_pages
from agenda.gui import template_model
from agenda.gui.template_model import preview_mode, sample_plan
from agenda.templates import GLOBAL, STYLING, TEMPLATE_KEYS, section


@pytest.mark.parametrize("key", TEMPLATE_KEYS)
def test_sample_plan_renders(key):
    cfg = Config()
    plan = sample_plan(cfg, key)
    assert isinstance(plan, PagePlan)
    cls = get_page(section(key).page_id)
    assert all(e.page_class in (cls, None) for e in plan)
    assert any(e.page_class is cls for e in plan)
    pdf = render_pages(cfg, plan, range(len(plan)))
    assert len(PdfReader(io.BytesIO(pdf)).pages) == len(plan)


def test_weekly_pair():
    plan = sample_plan(Config(), "weekly")
    drawn = [e for e in plan if e.page_class is not None]
    assert [e.side for e in drawn] == ["left", "right"]
    assert len(plan.drawn()) == 1


def test_daily_month():
    d = sample_plan(Config(daily_months=[3]), "daily")[0].ctx["date"]
    assert (d.month, d.day) == (3, 1)


def test_daily_quote(tmp_path):
    f = tmp_path / "q.txt"
    f.write_text("Alpha phrase\nBeta phrase\n", encoding="utf-8")
    cfg = Config(daily_quotes=True, daily_quotes_file=f)
    plan = sample_plan(cfg, "daily")
    text = PdfReader(io.BytesIO(render_pages(cfg, plan, [0]))).pages[0].extract_text()
    first = plan[0].ctx["date"]
    assert first.month == 1 and first.day == 1
    assert "Alpha phrase" in text


def test_disabled_and_keys():
    assert len(sample_plan(Config(planners=["weekly"]), "daily")) == 1
    assert len(sample_plan(Config(contacts_pages=0), "contacts")) >= 1
    for k in [
        "notes",
        "daily",
        "weekly",
        "contacts",
        "schedule",
        "habits",
        "qr",
        "niche_entrepreneur",
        "niche_student",
        "niche_fitness",
    ]:
        assert k in TEMPLATE_KEYS


def test_modes():
    assert preview_mode("weekly") == "spread"
    assert preview_mode("daily") == "single"


def test_sample_plan_errors():
    for k in (GLOBAL, STYLING, "nope"):
        with pytest.raises(ValueError):
            sample_plan(Config(), k)


def test_no_qt():
    assert "PySide6" not in Path(template_model.__file__).read_text()
