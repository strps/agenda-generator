"""``AgendaGenerator.exe --self-test``: run the frozen app's data-file paths, report, exit 0/1.

The exe has no console, so the report is written to ``self-test.log`` in the current
directory. CI runs it on the built artifact; files PyInstaller missed (fonts, icons, the
holidays translations) fail here instead of on a user's machine.
"""

import os
import tempfile
import traceback
from datetime import date
from pathlib import Path


def _checks(log) -> None:
    from agenda.calendar import holidays_for

    for country, lang, day in (("CR", "es", date(2027, 9, 15)), ("CR", "en", date(2027, 9, 15))):
        log(f"holidays {country} {lang}: {holidays_for(2027, country, lang)[day]}")

    from agenda.catalog import catalog_rows
    from agenda.config import Config
    from agenda.exporter import export_agenda

    tmp = Path(tempfile.mkdtemp())
    pages = [str(r["id"]) for r in catalog_rows()]
    cfg = Config(year=2027, pages=pages, qr_urls=["https://example.com"], imposition=True)
    out = export_agenda(cfg, tmp / "agenda.pdf")
    log(f"export: {out.stat().st_size} bytes")

    import pypdfium2 as pdfium

    log(f"pdfium: {len(pdfium.PdfDocument(str(out)))} pages")

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from agenda.gui import style_model as SM
    from agenda.gui.app import MainWindow, apply_style

    # The stylesheet references the icons by path, so a missing one fails silently.
    names = [f"{kind}_{look}.svg" for kind in ("check", "pad") for look in ("dark", "light")]
    missing = [n for n in names if not (SM.ICONS / n).is_file()]
    if missing:
        raise RuntimeError(f"GUI icons missing from {SM.ICONS}: {missing}")
    log(f"icons: {len(names)}")
    app = QApplication.instance() or QApplication([])
    for look in SM.APPEARANCES:
        apply_style(app, look)
    win = MainWindow(QSettings(str(tmp / "prefs.ini"), QSettings.Format.IniFormat))
    win.show()
    win.preview.wait_idle()
    for pv in win.template_previews.values():
        pv.wait_idle()
    win.close()
    log("gui: ok")


def run(log_path: str = "self-test.log") -> int:
    lines: list[str] = []
    try:
        _checks(lines.append)
        lines.append("PASS")
        code = 0
    except Exception:  # noqa: BLE001 - any failure must reach the log and exit code
        lines.append(traceback.format_exc())
        lines.append("FAIL")
        code = 1
    Path(log_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return code
