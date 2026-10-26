import pytest
from pypdf import PdfReader

from agenda.cli import main
from agenda.config import Config
from agenda.exporter import export_agenda
from agenda.numbering import align_for, label_for, x_for

SMALL = {"year": 2026, "planners": ["weekly"], "daily_months": []}


def texts(path):
    return [p.extract_text() for p in PdfReader(str(path)).pages]


def test_numbers_printed_from_first_page(tmp_path):
    cfg = Config(**SMALL, page_numbers=True, page_number_first=3, page_number_format="Pg {n}x")
    out = export_agenda(cfg, tmp_path / "a.pdf")
    t = texts(out)
    assert "Pg 3x" in t[4]  # plan page 5 -> number 5 (start 1 at page 3 -> 3)
    assert not any("Pg " in x for x in t[:2])
    assert "Pg 1x" in t[2]


def test_label_on_page_5_default(tmp_path):
    cfg = Config(**SMALL, page_numbers=True, page_number_format="<{n}>")
    t = texts(export_agenda(cfg, tmp_path / "a.pdf"))
    assert "<5>" in t[4]


def test_off_has_no_label(tmp_path):
    cfg = Config(**SMALL, page_numbers=False, page_number_format="<{n}>")
    assert not any("<" in x for x in texts(export_agenda(cfg, tmp_path / "a.pdf")))


def test_cli_start_and_format(tmp_path):
    out = tmp_path / "c.pdf"
    code = main(["--year", "2026", "--planners", "weekly", "--daily-months", "",
                 "--page-numbers", "--page-number-start", "10",
                 "--page-number-format", "{n} / {total}", "--output", str(out)])
    assert code == 0
    assert "10 / " in texts(out)[0]


def test_footer_placement(tmp_path):
    cfg = Config(**SMALL, page_numbers=True, page_number_placement="footer",
                 page_number_format="<{n}>")
    assert "<5>" in texts(export_agenda(cfg, tmp_path / "f.pdf"))[4]


@pytest.mark.parametrize("bad", ["x", "{n}{m}", "{", "{n:", "", "a" * 25, "{total}"])
def test_bad_format_rejected(bad):
    with pytest.raises(ValueError):
        Config(page_number_format=bad)


def test_label_for():
    cfg = Config(page_numbers=True, page_number_start=10, page_number_first=3,
                 page_number_format="{n}/{total}")
    assert label_for(cfg, 2, 20) is None
    assert label_for(cfg, 3, 20) == "10/27"
    assert label_for(cfg, 4, 20) == "11/27"
    assert label_for(Config(), 1, 20) is None


def test_align_and_x():
    assert [align_for("right", p) for p in ("outer", "center", "inner")] == ["R", "C", "L"]
    assert [align_for("left", p) for p in ("outer", "center", "inner")] == ["L", "C", "R"]
    assert x_for("right", "outer", 15, 100, 10) == 105
    assert x_for("left", "outer", 10, 100, 10) == 10
    assert x_for("right", "center", 15, 100, 10) == 60
    assert x_for("left", "inner", 10, 100, 10) == 100
