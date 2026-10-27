"""Main window shell and entry point. Regions are empty placeholders filled by later tasks."""

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QThreadPool, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QKeySequence, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from agenda.assembler import build_plan, summarize
from agenda.configfile import ConfigFileError
from agenda.gui import export_model as EM
from agenda.gui import help_text as HT
from agenda.gui import layout as L
from agenda.gui import legend_model as LM
from agenda.gui import style_model as SM
from agenda.gui import template_model as TM
from agenda.gui.export_dialog import ExportDialog
from agenda.gui.export_job import ExportJob, ExportSignals
from agenda.gui.legend import Legend
from agenda.gui.prefs_dialog import GuiSettingsDialog
from agenda.gui.preview import PreviewWidget
from agenda.gui.render_cache import Debounce
from agenda.gui.section_bar import SectionBar
from agenda.gui.settings_panel import SettingsPanel
from agenda.pagerange import parse_page_range
from agenda.templates import GLOBAL, TEMPLATE_KEYS, is_enabled, section_label
from agenda.uitext import tr

DEBOUNCE_S = 0.3  # settings edits settle this long before the preview re-renders


PREFS_ORG, PREFS_APP, PREFS_KEY = "agenda-gen", "agenda-gui", "appearance"
PREF_OPEN_AFTER, PREF_LAST_DIR = "export/open_after", "export/last_dir"


def apply_style(app: QApplication, appearance: str = SM.DEFAULT_APPEARANCE) -> bool:
    """Apply the stylesheet and a matching palette; returns True when the dark theme is used."""
    lightness = app.palette().color(QPalette.ColorRole.Window).lightness()
    dark = SM.resolve_dark(appearance, lightness)
    t = SM.THEMES["dark" if dark else "light"]
    pal = QPalette()
    for role, key in (
        (QPalette.ColorRole.Window, "window"),
        (QPalette.ColorRole.WindowText, "text"),
        (QPalette.ColorRole.Base, "input_bg"),
        (QPalette.ColorRole.AlternateBase, "panel"),
        (QPalette.ColorRole.Text, "text"),
        (QPalette.ColorRole.Button, "input_bg"),
        (QPalette.ColorRole.ButtonText, "text"),
        (QPalette.ColorRole.Highlight, "accent"),
        (QPalette.ColorRole.HighlightedText, "accent_text"),
        (QPalette.ColorRole.ToolTipBase, "tooltip_bg"),
        (QPalette.ColorRole.ToolTipText, "tooltip_text"),
    ):
        pal.setColor(role, QColor(t[key]))
    app.setPalette(pal)
    app.setStyleSheet(SM.stylesheet(dark))
    return dark


class MainWindow(QMainWindow):
    """Window shell. `regions` maps each name in `layout.REGIONS` to its container widget."""

    def __init__(self, prefs: QSettings | None = None) -> None:
        super().__init__()
        self.prefs = prefs if prefs is not None else QSettings(PREFS_ORG, PREFS_APP)
        saved = str(self.prefs.value(PREFS_KEY, SM.DEFAULT_APPEARANCE))
        self.appearance = saved if saved in SM.APPEARANCES else SM.DEFAULT_APPEARANCE
        spec = L.WindowLayout()
        self.setWindowTitle(spec.title)
        self.resize(spec.width, spec.height)
        self.setMinimumSize(spec.min_width, spec.min_height)

        self.regions: dict[str, QWidget] = {}
        root = QWidget()
        col = QVBoxLayout(root)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        # Top toolbar: open/save on the left, export on the right.
        toolbar = self._region(L.TOOLBAR)
        row = QHBoxLayout(toolbar)
        gap, margin = SM.SPACING["gap"], SM.SPACING["margin"]
        row.setContentsMargins(margin, gap, margin, gap)
        row.setSpacing(gap)
        self.open_button = QPushButton(tr("app.open_config"))
        self.save_button = QPushButton(tr("app.save_config"))
        self.open_button.setToolTip(HT.TOOLTIPS["open_config"])
        self.save_button.setToolTip(HT.TOOLTIPS["save_config"])
        row.addWidget(self.open_button)
        row.addWidget(self.save_button)
        row.addStretch(1)
        export = self._region(L.EXPORT)
        erow = QHBoxLayout(export)
        erow.setContentsMargins(0, 0, 0, 0)
        erow.setSpacing(gap)
        self.export_button = QPushButton(tr("app.export_pdf"))
        self.export_button.setObjectName("export_button")
        self.export_progress = QProgressBar()
        self.export_progress.setRange(0, 100)
        self.export_progress.setFixedWidth(140)
        self.export_progress.hide()
        self.export_status = QLabel()
        erow.addWidget(self.export_status)
        erow.addWidget(self.export_progress)
        self.export_button.setToolTip(HT.TOOLTIPS["export_pdf"])
        erow.addWidget(self.export_button)
        self.export_running = False
        self._export_pool = QThreadPool()
        self._export_signals: ExportSignals | None = None
        self._export_interactive = False
        self._open_after = False
        self._last_page_range = ""
        row.addWidget(export)
        col.addWidget(toolbar)

        # Middle: settings (left) | preview (center).
        split = QSplitter(Qt.Orientation.Horizontal)
        self.settings = SettingsPanel()
        self.regions[L.SETTINGS] = self.settings
        split.addWidget(self.settings)
        self.preview = PreviewWidget()
        self.regions[L.PREVIEW] = self.preview
        self.preview_stack = QStackedWidget()
        self.preview_stack.addWidget(self.preview)
        self.template_previews: dict[str, PreviewWidget] = {}
        self.template_notices: dict[str, QLabel] = {}
        self._template_pages: dict[str, QWidget] = {}
        for key in TEMPLATE_KEYS:
            page = QWidget()
            page.setObjectName(f"template_page_{key}")
            lay = QVBoxLayout(page)
            lay.setContentsMargins(0, 0, 0, 0)
            notice = QLabel("")
            notice.setObjectName(f"template_notice_{key}")
            notice.setWordWrap(True)
            pv = PreviewWidget()
            pv.set_mode(TM.preview_mode(key))
            lay.addWidget(notice)
            lay.addWidget(pv, 1)
            self.preview_stack.addWidget(page)
            self.template_previews[key] = pv
            self.template_notices[key] = notice
            self._template_pages[key] = page
        self.preview_key = GLOBAL
        self.last_template: str | None = None
        self._stale: set[str] = set(TEMPLATE_KEYS)
        split.addWidget(self.preview_stack)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes(list(spec.splitter_sizes()))
        col.addWidget(split, 1)

        # Bottom: section bar, legend, summary.
        self.section_bar = SectionBar()
        self.regions[L.SECTION_BAR] = self.section_bar
        col.addWidget(self.section_bar)
        self.legend = Legend()
        self.legend.setObjectName(L.LEGEND)
        self.regions[L.LEGEND] = self.legend
        col.addWidget(self.legend)
        self.summary_label = QLabel()
        self.summary_label.setObjectName(L.SUMMARY)
        self.summary_label.setContentsMargins(4, 2, 4, 2)
        self.regions[L.SUMMARY] = self.summary_label
        col.addWidget(self.summary_label)
        self.setCentralWidget(root)
        self.debounce = Debounce(DEBOUNCE_S)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(int(DEBOUNCE_S * 1000))
        self._timer.timeout.connect(self.update_preview)
        self.settings.changed.connect(self._on_settings_changed)
        self.preview.page_changed.connect(self.section_bar.set_position)
        self.section_bar.page_requested.connect(self.preview.goto)
        self.section_bar.page_requested.connect(lambda _i: self.show_preview_for(GLOBAL))
        self.legend.section_clicked.connect(self.section_bar.next_page_of)
        self.legend.section_clicked.connect(lambda _k: self.show_preview_for(GLOBAL))
        self.settings.section_activated.connect(self.show_preview_for)
        menu = self.menuBar().addMenu(tr("app.menu_settings"))
        self.preferences_action = QAction(tr("app.preferences"), self)
        self.preferences_action.setObjectName("action_preferences")
        self.preferences_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences))
        self.preferences_action.setToolTip(HT.TOOLTIPS["preferences"])
        self.preferences_action.setStatusTip(HT.TOOLTIPS["preferences"])
        self.preferences_action.triggered.connect(lambda _checked=False: self.open_preferences())
        menu.addAction(self.preferences_action)
        self.update_preview()
        self.open_button.clicked.connect(self.open_config_dialog)
        self.save_button.clicked.connect(self.save_config_dialog)
        self.export_button.clicked.connect(self.export_dialog)

    def open_preferences(self) -> None:
        """Show the GUI Settings dialog; apply and persist the appearance on accept."""
        dlg = GuiSettingsDialog(self.appearance, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._set_appearance(dlg.appearance())

    def _set_appearance(self, appearance: str) -> None:
        """User picked an appearance: restyle the running app and remember the choice."""
        self.appearance = appearance
        app = QApplication.instance()
        if app is not None:
            apply_style(app, appearance)
        self.prefs.setValue(PREFS_KEY, appearance)
        self.prefs.sync()

    def _on_settings_changed(self) -> None:
        self.debounce.push()
        self._timer.start()

    def flush_preview(self) -> None:
        """Apply a pending settings change now (skips the debounce wait)."""
        if self.debounce.pending:
            self.update_preview()

    def update_preview(self) -> None:
        """Rebuild the plan from the current settings; pages render in the worker thread."""
        self._timer.stop()
        self.debounce.flush()
        cfg, msg = self.settings.config()
        if cfg is None:
            self.preview.set_error(msg)
            for pv in self.template_previews.values():
                pv.set_error(msg)
            self._stale = set(TEMPLATE_KEYS)
            self.legend.set_entries([])
            self.summary_label.setText(LM.NO_PLAN_TEXT)
            self.summary_label.setToolTip("")
            self._sync_export_button(valid=False)
            return
        plan = build_plan(cfg)
        info = summarize(plan, cfg)
        self.legend.set_entries(LM.legend_entries(plan))
        self.summary_label.setText(LM.summary_text(info))
        self.summary_label.setToolTip(LM.summary_tooltip(info))
        self.section_bar.set_plan(plan)
        self.preview.set_plan(cfg, plan)
        self.section_bar.set_position(self.preview.index)
        self._update_templates(cfg)
        self._sync_export_button(valid=True)

    def _update_templates(self, cfg) -> None:
        """Refresh enable state of all template previews, and the plan of the visible one."""
        for key in TEMPLATE_KEYS:
            off = not is_enabled(cfg, key)
            self.template_previews[key].set_inactive(off)
            self.template_notices[key].setText(
                tr("app.template_disabled", label=section_label(key)) if off else ""
            )
        self._stale = set(TEMPLATE_KEYS)
        if self.preview_key in TEMPLATE_KEYS:
            self._refresh_template(self.preview_key, cfg)

    def _refresh_template(self, key: str, cfg) -> None:
        self.template_previews[key].set_plan(cfg, TM.sample_plan(cfg, key))
        self._stale.discard(key)

    def show_preview_for(self, key: str) -> None:
        """Show the full agenda preview or the preview of the template for section ``key``."""
        if key in TEMPLATE_KEYS:
            self.last_template = key
        target = TM.preview_target(key, self.last_template)
        self.preview_key = target
        if target in TEMPLATE_KEYS:
            self.preview_stack.setCurrentWidget(self._template_pages[target])
            if target in self._stale:
                cfg, msg = self.settings.config()
                if cfg is None:
                    self.template_previews[target].set_error(msg)
                else:
                    self._refresh_template(target, cfg)
        else:
            self.preview_stack.setCurrentWidget(self.preview)

    def _sync_export_button(self, valid: bool) -> None:
        self.export_button.setEnabled(valid and not self.export_running)
        tip = HT.TOOLTIPS["export_pdf"]
        if not valid:
            tip = f"{tip}\n\n{HT.EXPORT_DISABLED_REASON}"
        self.export_button.setToolTip(tip)

    def export_dialog(self) -> None:
        """Open the export dialog; on accept apply its values and export in the background."""
        cfg, _ = self.settings.config()
        if cfg is None or self.export_running:
            return
        values = self.settings.values()
        values["output"] = self._default_output(cfg)
        dlg = ExportDialog(
            values,
            total_pages=len(build_plan(cfg)),
            open_after=self.prefs.value(PREF_OPEN_AFTER, False, type=bool),
            page_range=self._last_page_range,
            parent=self,
        )
        if not dlg.exec():
            return
        self._last_page_range = dlg.page_range()
        self.prefs.setValue(PREF_OPEN_AFTER, dlg.open_after())
        result = dlg.result_values()
        self.settings.set_values({**self.settings.values(), **result})
        self.flush_preview()
        out = str(result["output"])
        if Path(out).parent != Path():
            self.prefs.setValue(PREF_LAST_DIR, str(Path(out).parent))
        self.prefs.sync()
        self._open_after = dlg.open_after()
        self.start_export(out, interactive=True, page_range=self._last_page_range)

    def _default_output(self, cfg) -> str:
        path = EM.default_path(cfg)
        last = str(self.prefs.value(PREF_LAST_DIR, "") or "")
        return str(Path(last) / Path(path).name) if last else path

    def open_file(self, path: str) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def start_export(self, path: str, interactive: bool = False, page_range: str = "") -> bool:
        """Export the current settings to ``path`` off the GUI thread. False if not started."""
        cfg, _ = self.settings.config()
        if cfg is None or self.export_running:
            return False
        pages = None
        if page_range.strip():
            try:
                pages = parse_page_range(page_range, len(build_plan(cfg)))
            except ValueError:
                return False
        self.export_running, self._export_interactive = True, interactive
        self.export_result = ""
        sig = self._export_signals = ExportSignals()
        sig.progress.connect(self._on_export_progress)
        sig.done.connect(self._on_export_done)
        sig.failed.connect(self._on_export_failed)
        self.export_progress.setValue(0)
        self.export_progress.show()
        self.export_status.setText(tr("app.exporting"))
        self._sync_export_button(valid=True)
        self._export_pool.start(ExportJob(cfg, str(EM.ensure_pdf(path)), sig, pages))
        return True

    def wait_export(self, timeout: float = 120.0) -> bool:
        """Process events until the export ends (for tests). False on timeout."""
        import time

        end = time.monotonic() + timeout
        while self.export_running and time.monotonic() < end:
            QApplication.processEvents()
            time.sleep(0.005)
        return not self.export_running

    def _on_export_progress(self, done: int, total: int) -> None:
        self.export_progress.setValue(EM.progress_percent(done, total))

    def _finish_export(self, text: str, ok: bool) -> None:
        self.export_running = False
        self.export_progress.hide()
        self.export_status.setText(text)
        self.export_result = text
        cfg, _ = self.settings.config()
        self._sync_export_button(valid=cfg is not None)
        if self._export_interactive:
            box = QMessageBox.information if ok else QMessageBox.warning
            box(self, tr("app.export_pdf"), text)

    def _on_export_done(self, path: str) -> None:
        self.export_progress.setValue(100)
        self._finish_export(tr("app.exported", path=path), True)
        if self._export_interactive and self._open_after:
            self.open_file(path)

    def _on_export_failed(self, msg: str) -> None:
        self._finish_export(tr("app.export_failed", message=msg), False)

    def load_config(self, path: str) -> str:
        """Load a YAML file into the settings panel. Returns "" or the error message."""
        try:
            self.settings.load_file(path)
        except ConfigFileError as exc:
            return str(exc)
        return ""

    def save_config(self, path: str) -> str:
        """Save the settings as YAML. Returns "" or the error message."""
        return self.settings.save_file(path)

    def open_config_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("app.open_config"), "", tr("app.yaml_open_filter")
        )
        if path and (err := self.load_config(path)):
            QMessageBox.warning(self, tr("app.open_config"), err)

    def save_config_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("app.save_config"), "config.yaml", tr("app.yaml_save_filter")
        )
        if path and (err := self.save_config(path)):
            QMessageBox.warning(self, tr("app.save_config"), err)

    def _region(self, name: str) -> QWidget:
        w = QWidget()
        w.setObjectName(name)
        self.regions[name] = w
        return w

    def _placeholder(self, name: str, text: str, height: int | None = None) -> QWidget:
        frame = QFrame()
        frame.setObjectName(name)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.addWidget(QLabel(text), alignment=Qt.AlignmentFlag.AlignCenter)
        if height is not None:
            frame.setFixedHeight(height)
        self.regions[name] = frame
        return frame


def main(argv: list[str] | None = None) -> int:
    """Entry point for `agenda-gui` and `python -m agenda.gui`."""
    app = QApplication.instance() or QApplication(sys.argv if argv is None else argv)
    prefs = QSettings(PREFS_ORG, PREFS_APP)
    saved = str(prefs.value(PREFS_KEY, SM.DEFAULT_APPEARANCE))
    apply_style(app, saved if saved in SM.APPEARANCES else SM.DEFAULT_APPEARANCE)
    win = MainWindow(prefs)
    win.show()
    return app.exec()
