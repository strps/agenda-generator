"""Phase 11: hard-coded page values are Config settings with the old values as defaults."""

from __future__ import annotations

import io

import pytest
from pydantic import ValidationError
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.config import Config
from agenda.pages.core import Daily
from agenda.pages.optional import Habits, Schedule
from agenda.pages.value_added import PackEntrepreneur, PackFitness, PackStudent
from agenda.templates import group_of, section
from tests.helpers import render_page

NEW_FIELDS = {
    "daily_hour_start": ("daily", 6),
    "daily_hour_end": ("daily", 21),
    "schedule_first_hour": ("schedule", 7),
    "schedule_last_hour": ("schedule", 21),
    "habits_max": ("habits", 20),
    "niche_entrepreneur_pages": ("niche_entrepreneur", 1),
    "niche_student_pages": ("niche_student", 1),
    "niche_fitness_pages": ("niche_fitness", 1),
}


def text_of(pdf: bytes) -> str:
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)


def test_defaults_and_validation():
    cfg = Config()
    for name, (_, default) in NEW_FIELDS.items():
        assert getattr(cfg, name) == default
    with pytest.raises(ValidationError, match="daily_hour_start"):
        Config(daily_hour_start=21, daily_hour_end=6)
    with pytest.raises(ValidationError, match="schedule_first_hour"):
        Config(schedule_first_hour=25)
    with pytest.raises(ValidationError, match="schedule_first_hour"):
        Config(schedule_first_hour=21, schedule_last_hour=21)
    with pytest.raises(ValidationError, match="habits_max"):
        Config(habits_max=0)
    with pytest.raises(ValidationError, match="niche_student_pages"):
        Config(niche_student_pages=21)


@pytest.mark.parametrize("cls", [Daily, Schedule, Habits, PackEntrepreneur, PackStudent, PackFitness])
def test_defaults_render_like_explicit_old_values(cls):
    explicit = Config(
        daily_hour_start=6,
        daily_hour_end=21,
        schedule_first_hour=7,
        schedule_last_hour=21,
        habits_max=20,
    )
    assert text_of(render_page(cls, Config())) == text_of(render_page(cls, explicit))


def test_default_hour_labels():
    daily = text_of(render_page(Daily, Config(daily_months=[1])))
    assert "06:00" in daily and "21:00" in daily and "05:00" not in daily
    assert "7:00" in text_of(render_page(Schedule, Config()))


def test_daily_hour_range():
    text = text_of(render_page(Daily, Config(daily_months=[1], daily_hour_start=8, daily_hour_end=12)))
    for h in range(8, 13):
        assert f"{h:02d}:00" in text
    assert "07:00" not in text and "13:00" not in text


def test_schedule_first_hour():
    text = text_of(render_page(Schedule, Config(schedule_first_hour=9)))
    assert "9:00" in text and "7:00" not in text.replace("17:00", "")


def test_schedule_last_hour_caps_rows():
    assert Schedule.layout(48, 5) == (5, 3)
    assert Schedule.layout(48) == (15, 3)


def test_habits_layout():
    assert Habits.layout(100, 5) == 5
    assert Habits.layout(100) == 20


def test_niche_counts():
    plan = build_plan(Config(pages=["niche_student"], niche_student_pages=3))
    assert sum(e.page_class is PackStudent for e in plan.entries) == 3
    assert len(PackStudent(count=2).instances(Config())) == 2
    assert len(PackStudent().instances(Config())) == 1
    with pytest.raises(ValueError):
        PackStudent(count=-1)


def test_sections():
    for name, (key, _) in NEW_FIELDS.items():
        assert group_of(name) == key
    assert section("schedule").enable == "page"
    assert section("habits").enable == "page"
