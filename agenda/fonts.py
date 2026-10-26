"""PDF font selection (Qt-free): the bundled Inter or a user .ttf/.otf file with sibling styles."""

from __future__ import annotations

from pathlib import Path

FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
# fpdf2 style code -> file name of the bundled Inter.
FONT_FILES = {
    "": "Inter-Regular.ttf",
    "B": "Inter-Bold.ttf",
    "I": "Inter-Italic.ttf",
    "BI": "Inter-BoldItalic.ttf",
}
BUILTIN: dict[str, dict[str, Path]] = {"inter": {s: FONT_DIR / f for s, f in FONT_FILES.items()}}
STYLES = ("", "B", "I", "BI")
_WORDS = {"": "Regular", "B": "Bold", "I": "Italic", "BI": "BoldItalic"}


def resolve(spec: str) -> dict[str, Path]:
    """Map each style ("", "B", "I", "BI") to a font file for a built-in name or a font path.

    Siblings are found by swapping "Regular" in the file name for Bold/Italic/BoldItalic (or
    appending "-<Style>" when the stem has no "Regular"); missing styles use the regular file.
    Raises ValueError for unknown names, missing files and non-font files.
    """
    text = (spec or "").strip()
    if text.lower() in BUILTIN:
        return dict(BUILTIN[text.lower()])
    path = Path(text).expanduser()
    if not text or not path.is_file():
        known = ", ".join(BUILTIN)
        raise ValueError(
            f"unknown font {spec!r}: use a built-in name ({known}) or a .ttf/.otf file"
        )
    if path.suffix.lower() not in (".ttf", ".otf"):
        raise ValueError(f"font file {spec!r} must be a .ttf or .otf file")
    out = {"": path}
    stem = path.stem
    for style in STYLES[1:]:
        word = _WORDS[style]
        names = [stem.replace("Regular", word)] if "Regular" in stem else []
        names.append(f"{stem}-{word}")
        for name in names:
            cand = path.with_name(name + path.suffix)
            if name != stem and cand.is_file():
                out[style] = cand
                break
        else:
            out[style] = path
    return out
