import pytest

from agenda.config import Config
from agenda.exporter import add_page, new_document, write_pdf
from agenda.pages.base import BasePage


def make(**attrs):
    body = {"id": "dummy", "name": "Dummy", "category": "core", "section": "monthly", **attrs}
    body["draw"] = lambda self, pdf, ctx, config, grids: None
    return type("Dummy", (BasePage,), body)


def test_defaults():
    cls = make()
    assert (cls.pages, cls.starts_on) == (1, "any")
    assert cls().instances(Config()) == [{}]


def test_abstract_draw_required():
    with pytest.raises(TypeError):
        BasePage()  # type: ignore[abstract]


def test_abstract_intermediate_may_omit_attrs():
    class Mid(BasePage):
        pass  # still abstract: draw missing

    with pytest.raises(TypeError):
        Mid()  # type: ignore[abstract]


@pytest.mark.parametrize(
    "attrs",
    [
        {"section": "nope"},
        {"category": "nope"},
        {"starts_on": "middle"},
        {"pages": 0},
        {"pages": 1.5},
        {"pages": True},
        {"id": ""},
        {"name": 3},
    ],
)
def test_invalid_attributes(attrs):
    with pytest.raises(ValueError):
        make(**attrs)


def test_missing_attribute():
    with pytest.raises(ValueError, match="section"):
        type(
            "NoSection",
            (BasePage,),
            {
                "id": "x",
                "name": "X",
                "category": "core",
                "draw": lambda self, pdf, ctx, config, grids: None,
            },
        )


def test_instances_override_and_draw_valid_pdf(tmp_path):
    class Months(make(pages=2, starts_on="left", section="weekly")):
        id = "months"

        def instances(self, config):
            return [{"month": m} for m in range(1, 4)]

        def draw(self, pdf, ctx, config, grids):
            pdf.set_xy(grids[0].safe.x, grids[0].safe.y)
            pdf.set_font("helvetica", size=10)
            pdf.cell(20, 5, f"m{ctx['month']}")

    cfg = Config()
    page, pdf = Months(), new_document(cfg)
    for ctx in page.instances(cfg):
        grids = [add_page(pdf, cfg) for _ in range(page.pages)]
        page.draw(pdf, ctx, cfg, grids)
    assert pdf.page == 6
    out = write_pdf(pdf, tmp_path / "x.pdf")
    assert out.read_bytes().startswith(b"%PDF")
