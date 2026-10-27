"""Pure layout description of the main window (no Qt), see docs/architecture/gui.md section 1."""

from dataclasses import dataclass, field

from agenda.uitext import tr

# Placeholder regions, top to bottom / left to right. Later tasks fill them.
TOOLBAR = "toolbar"
SETTINGS = "settings"
PREVIEW = "preview"
SECTION_BAR = "section_bar"
LEGEND = "legend"
SUMMARY = "summary"
EXPORT = "export"

REGIONS = (TOOLBAR, SETTINGS, PREVIEW, SECTION_BAR, LEGEND, SUMMARY, EXPORT)


@dataclass(frozen=True)
class WindowLayout:
    title: str = field(default_factory=lambda: tr("app.title"))
    width: int = 1200
    height: int = 800
    settings_width: int = 320
    min_width: int = 800
    min_height: int = 500

    def splitter_sizes(self) -> tuple[int, int]:
        """Initial (settings, preview) widths; settings keeps a fixed share, preview the rest."""
        return (self.settings_width, self.width - self.settings_width)
