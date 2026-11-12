"""Qt-free help texts: toolbar tooltips and section descriptions (plain text, no HTML)."""

from collections.abc import Callable, Iterator, Mapping

from agenda.config import Config
from agenda.fields import detail_help, field_names, short_help
from agenda.gui.bar_model import SECTION_LABELS
from agenda.uitext import Table, tr

TOOLTIPS: Mapping[str, str] = Table(
    "tooltip",
    (
        "open_config",
        "save_config",
        "export_pdf",
        "prev",
        "next",
        "mode_single",
        "mode_spread",
        "mode_sheet",
        "appearance",
        "ui_language",
        "color_swatch",
        "color_clear",
        "font_browse",
        "file_browse",
        "file_clear",
        "global_section",
        "padding_section",
        "month_start_section",
        "month_end_section",
        "styling_section",
        "preferences",
        "zoom",
    ),
)
EXPORT_HELP: Mapping[str, str] = Table(
    "export.help",
    (
        "page_range",
        "page_range_detail",
        "layout_pages",
        "layout_pages_detail",
        "layout_spreads",
        "layout_spreads_detail",
        "layout_booklets",
        "layout_booklets_detail",
        "open_after",
        "open_after_detail",
        "cli_preview",
        "cli_preview_detail",
        "browse_output",
        "browse_output_detail",
    ),
)
SECTION_DESCRIPTIONS: Mapping[str, str] = Table(
    "section_desc",
    ("front_back", "monthly", "weekly", "daily", "optional", "value_added", "padding"),
)


def __getattr__(name: str) -> str:
    if name == "EXPORT_DISABLED_REASON":
        return tr("export.disabled_reason")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def section_tooltip(key: str) -> str:
    """ "<Label>: <description>" for a section key; unknown keys fall back to the key."""
    label = SECTION_LABELS.get(key, key)
    desc = SECTION_DESCRIPTIONS.get(key)
    return f"{label}: {desc}" if desc else label


# Short and detailed texts for every Config field live on the fields themselves (agenda.config).
class _FieldTexts(Mapping[str, str]):
    """Read-only mapping field name -> text, resolved in the current UI language on access."""

    def __init__(self, getter: Callable[[str], str]) -> None:
        self._getter = getter

    def __getitem__(self, name: str) -> str:
        if name not in Config.model_fields:
            raise KeyError(name)
        return self._getter(name)

    def __iter__(self) -> Iterator[str]:
        return iter(field_names())

    def __len__(self) -> int:
        return len(Config.model_fields)


PARAM_SHORT: Mapping[str, str] = _FieldTexts(short_help)
PARAM_DETAILS: Mapping[str, str] = _FieldTexts(detail_help)


def param_tooltip(name: str, expanded: bool = False) -> str:
    """Short text for a Config field, plus detail after a newline when expanded."""
    short = PARAM_SHORT.get(name)
    if short is None:
        return name
    detail = PARAM_DETAILS.get(name)
    return f"{short}\n{detail}" if expanded and detail else short
