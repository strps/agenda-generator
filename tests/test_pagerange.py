import pytest

from agenda.pagerange import format_page_range, parse_page_range


def test_parse():
    assert parse_page_range("1-3, 5", 10) == [1, 2, 3, 5]
    assert parse_page_range(" 5 ,2,2-3 ", 10) == [2, 3, 5]


@pytest.mark.parametrize("text", ["", "all", " ALL ", None])
def test_all(text):
    assert parse_page_range(text, 10) is None


@pytest.mark.parametrize("text,token", [("0", "0"), ("4-2", "4-2"), ("11", "11"), ("a", "a"), ("1,x-3", "x-3")])
def test_bad(text, token):
    with pytest.raises(ValueError, match=token):
        parse_page_range(text, 10)


def test_format():
    assert format_page_range([5, 1, 2, 3, 3]) == "1-3,5"
    assert format_page_range([]) == ""
