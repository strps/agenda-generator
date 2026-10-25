import pytest

from agenda import catalog
from agenda.catalog import all_pages, get_page, pages_by_category, register, resolve_pages
from agenda.config import Config
from agenda.pages.base import BasePage


@pytest.fixture(autouse=True)
def isolated_registry():
    saved = dict(catalog.CATALOG)
    yield
    catalog.CATALOG.clear()
    catalog.CATALOG.update(saved)


def make(id, category="core", **attrs):
    body = {"id": id, "name": id, "category": category, "section": "monthly", **attrs}
    body["draw"] = lambda self, pdf, ctx, config, grids: None
    return type(f"P_{id}", (BasePage,), body)


def test_register_returns_class_and_looks_up():
    cls = register(make("t_a"))
    assert get_page("t_a") is cls
    assert cls in all_pages()


def test_decorator_syntax():
    @register
    class Mine(BasePage):
        id, name, category, section = "t_b", "B", "optional", "optional"

        def draw(self, pdf, ctx, config, grids): ...

    assert get_page("t_b") is Mine


def test_duplicate_id_errors():
    register(make("t_dup"))
    with pytest.raises(ValueError, match="t_dup"):
        register(make("t_dup"))


def test_non_basepage_errors():
    with pytest.raises(TypeError):
        register(int)  # type: ignore[type-var]
    with pytest.raises(TypeError):
        register(object())  # type: ignore[type-var]


def test_unknown_id_lists_valid_ids():
    register(make("t_c"))
    with pytest.raises(KeyError, match="t_c"):
        get_page("nope")


def test_registration_order_and_category():
    a, b, c = register(make("t_1")), register(make("t_2", "optional")), register(make("t_3"))
    ids = [p.id for p in all_pages()]
    assert ids.index("t_1") < ids.index("t_2") < ids.index("t_3")
    core = pages_by_category("core")
    assert [p for p in core if p in (a, b, c)] == [a, c]
    with pytest.raises(ValueError):
        pages_by_category("bogus")


def test_resolve_pages():
    a, b = register(make("t_x")), register(make("t_y", "optional"))
    assert a in resolve_pages(Config()) and b not in resolve_pages(Config())
    assert resolve_pages(Config(pages=["t_y", "t_x"])) == [b, a]
    with pytest.raises(KeyError):
        resolve_pages(Config(pages=["missing"]))
