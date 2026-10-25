import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.value_added import PackEntrepreneur, PackFitness, PackStudent

SIZES = ("a5", "b6", "letter")
PACKS = (
    (PackEntrepreneur, "niche_entrepreneur", "Weekly dashboard", "Panel semanal", "entre"),
    (PackStudent, "niche_student", "Courses & exams", "Cursos y exámenes", "student"),
    (PackFitness, "niche_fitness", "Workout log", "Registro de entrenamiento", "fitness"),
)
ids = [p[1] for p in PACKS]


@pytest.mark.parametrize(("cls", "pid"), [(p[0], p[1]) for p in PACKS], ids=ids)
def test_registered(cls, pid):
    assert get_page(pid) is cls
    assert cls in pages_by_category("value_added")
    assert (cls.category, cls.section, cls.pages) == ("value_added", "value_added", 1)


@pytest.mark.parametrize("cls", [p[0] for p in PACKS], ids=ids)
def test_count(cls):
    assert len(cls().instances(Config())) == 1
    assert len(cls(count=3).instances(Config())) == 3
    assert cls(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        cls(count=-1)


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("cls", [p[0] for p in PACKS], ids=ids)
def test_renders_inside_safe_area(cls, size, lang):
    cfg = Config(language=lang, page_size=size)
    data = render_page(cls, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize(("cls", "pid", "en", "es", "prefix"), PACKS, ids=ids)
def test_localized_title_and_strings(cls, pid, en, es, prefix):
    for lang, title in (("en", en), ("es", es)):
        text = (
            PdfReader(io.BytesIO(render_page(cls, Config(language=lang)))).pages[0].extract_text()
        )
        assert title in text
        s = Strings(lang)
        assert s(f"{prefix}.title") == title


@pytest.mark.parametrize(("cls", "pid"), [(p[0], p[1]) for p in PACKS], ids=ids)
def test_plan_only_when_listed(cls, pid):
    assert [e.page_class for e in build_plan(Config(pages=[pid]))].count(cls) == 1
    assert cls not in [e.page_class for e in build_plan(Config())]


def test_entrepreneur_layout():
    for rows in range(80):
        m, p, d = PackEntrepreneur.layout(rows)
        assert 1 <= m <= PackEntrepreneur.METRIC_MAX
        assert p >= 0 and d >= 0
    assert PackEntrepreneur.layout(PackEntrepreneur.FIXED_ROWS) == (1, 0, 0)
    m, p, d = PackEntrepreneur.layout(60)
    assert m == 4 and p == int((60 - 9 - 4) * 0.6) and p + d == 60 - 9 - 4


def test_student_layout():
    assert PackStudent.layout(0) == (0, False)
    t, study = PackStudent.layout(40)
    assert study and t == (40 - 1 - 5) // 2
    assert PackStudent.layout(8) == (3, False)
    for rows in range(80):
        t, study = PackStudent.layout(rows)
        used = 1 + t * 2 + (5 if study else 0)
        assert used <= max(rows, 1)


def test_fitness_layout():
    assert PackFitness.layout(0) == (0, 0)
    e, n = PackFitness.layout(44)
    assert n == 8 and e == (40 - 8) // 2
    for rows in range(80):
        e, n = PackFitness.layout(rows)
        assert 4 + e * 2 + n <= max(rows, 4)


@pytest.mark.parametrize("size", SIZES)
def test_layouts_nonempty_on_all_sizes(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    assert PackEntrepreneur.layout(rows).pipeline_rows >= 3
    assert PackStudent.layout(rows).table_rows >= 3
    assert PackFitness.layout(rows).exercise_rows >= 3
