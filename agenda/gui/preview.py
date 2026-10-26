"""Preview widget: single, spread and sheet modes; pages render in a worker thread, cached."""

import time

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from agenda.assembler import PagePlan
from agenda.config import Config
from agenda.gui import preview_model as M
from agenda.gui.help_text import TOOLTIPS
from agenda.gui.render_cache import LatestGate, LruCache, cache_key, config_hash
from agenda.gui.workers import RenderJob, RenderSignals, rasterise

__all__ = ["PreviewWidget", "rasterise"]


INACTIVE_OPACITY = 0.35


class PreviewWidget(QFrame):
    """Navigation bar (prev/next, label, mode, zoom) above a scroll area with the pages."""

    page_changed = Signal(int)  # current 0-based plan index

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("preview")
        self.cfg: Config | None = None
        self.plan: PagePlan | None = None
        self.index = 0
        self.mode = M.SPREAD
        self.zoom: str | int = M.FIT
        self._booklet_of: list[int | None] = []
        self.cache = LruCache(64)
        self._gate = LatestGate()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._signals = RenderSignals(self)
        self._signals.done.connect(self._on_done)
        self._signals.failed.connect(self._on_failed)
        self.busy = False
        self.inactive = False

        bar = QHBoxLayout()
        self.prev_button = QPushButton("◀")
        self.next_button = QPushButton("▶")
        self.prev_button.setToolTip(TOOLTIPS["prev"])
        self.next_button.setToolTip(TOOLTIPS["next"])
        self.label = QLabel("")
        bar.addWidget(self.prev_button)
        bar.addWidget(self.label, 1)
        self.mode_buttons: dict[str, QPushButton] = {}
        group = QButtonGroup(self)
        group.setExclusive(True)
        for m in M.MODES:
            b = QPushButton(m.capitalize())
            b.setToolTip(TOOLTIPS[f"mode_{m}"])
            b.setCheckable(True)
            b.setChecked(m == self.mode)
            group.addButton(b)
            bar.addWidget(b)
            self.mode_buttons[m] = b
            b.clicked.connect(lambda _=False, m=m: self.set_mode(m))
        bar.addWidget(self.next_button)
        self.zoom_box = QComboBox()
        for z in M.ZOOM_CHOICES:
            self.zoom_box.addItem("fit" if z == M.FIT else f"{z}%", z)
        self.zoom_box.setToolTip(TOOLTIPS["zoom"])
        bar.addWidget(self.zoom_box)

        self.canvas = QWidget()
        self.grid = QGridLayout(self.canvas)
        self.grid.setSpacing(8)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.canvas)
        self.message = QLabel("")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.addLayout(bar)
        lay.addWidget(self.message)
        lay.addWidget(self.scroll, 1)

        self.prev_button.clicked.connect(lambda: self.move(-1))
        self.next_button.clicked.connect(lambda: self.move(1))
        self.zoom_box.currentIndexChanged.connect(
            lambda _: self.set_zoom(self.zoom_box.currentData())
        )

    # -- state -------------------------------------------------------------------------------
    def set_plan(self, cfg: Config, plan: PagePlan) -> None:
        """Show ``plan`` (keeps the current page when still in range)."""
        self.cfg, self.plan = cfg, plan
        self._booklet_of = [e.booklet_index for e in plan.entries]
        self.index = min(self.index, max(len(plan) - 1, 0))
        self.refresh()

    def set_error(self, text: str) -> None:
        """Show ``text`` instead of the pages (e.g. an invalid config)."""
        self.cfg = self.plan = None
        self._gate.issue()
        self.busy = False
        self.message.setText(text)
        self._clear()
        self.label.setText("")

    def set_inactive(self, on: bool) -> None:
        """Gray the pages out (opacity effect on the scroll area) while ``on``."""
        self.inactive = on
        if on and self.scroll.graphicsEffect() is None:
            effect = QGraphicsOpacityEffect(self.scroll)
            effect.setOpacity(INACTIVE_OPACITY)
            self.scroll.setGraphicsEffect(effect)
        elif not on and self.scroll.graphicsEffect() is not None:
            self.scroll.setGraphicsEffect(None)

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.mode_buttons[mode].setChecked(True)
        self.refresh()

    def set_zoom(self, zoom: str | int) -> None:
        self.zoom = zoom
        self.zoom_box.setCurrentIndex(M.ZOOM_CHOICES.index(zoom))
        self.refresh()

    def goto(self, index: int) -> None:
        if self.plan is not None:
            self.index = min(max(index, 0), len(self.plan) - 1)
            self.refresh()

    def move(self, delta: int) -> None:
        if self.plan is not None:
            self.goto(M.step(self.mode, self.index, delta, *self._geometry()))

    def rows(self) -> list[list[int]]:
        """Plan indices currently shown, one list per row."""
        assert self.plan is not None
        return M.display_rows(self.mode, self.index, *self._geometry())

    def _geometry(self) -> tuple[int, list[int | None], bool]:
        assert self.plan is not None and self.cfg is not None
        return len(self.plan), self._booklet_of, self.cfg.booklet_folded

    # -- drawing -----------------------------------------------------------------------------
    def refresh(self) -> None:
        if self.plan is None or self.cfg is None or len(self.plan) == 0:
            return
        self.message.setText("")
        rows = self.rows()
        mode = M.effective_mode(self.mode, self.cfg.booklet_folded)
        self.label.setText(M.label(rows, len(self.plan), mode))
        self.mode_buttons[M.SHEET].setEnabled(self.cfg.booklet_folded)
        self._rows = rows
        need = M.render_indices(rows)
        cols = max(len(r) for r in rows)
        view = self.scroll.viewport()
        avail = (view.width(), view.height())
        self._zkey = (self.zoom, avail, len(rows), cols) if self.zoom == M.FIT else self.zoom
        self._hash = config_hash(self.cfg)
        missing = [i for i in need if cache_key(self._hash, i, self._zkey) not in self.cache]
        if not missing:
            self._gate.issue()  # drop any render still in flight
            self.busy = False
            self._show(rows)
            return
        self.busy = True
        job = RenderJob(
            self._gate.issue(), self._gate, self._signals, self.cfg, self.plan, missing,
            self.zoom, (len(rows), cols, avail),
        )  # fmt: skip
        self._pool.start(job)

    def wait_idle(self, timeout: float = 30.0) -> bool:
        """Process events until no render is pending (for tests/exports). False on timeout."""
        end = time.monotonic() + timeout
        while self.busy and time.monotonic() < end:
            QApplication.processEvents()
            time.sleep(0.005)
        return not self.busy

    def _on_done(self, request_id: int, images: dict[int, QImage]) -> None:
        if not self._gate.is_current(request_id):
            return  # result for an outdated request
        for i, img in images.items():
            self.cache.put(cache_key(self._hash, i, self._zkey), img)
        self.busy = False
        self._show(self._rows)

    def _on_failed(self, request_id: int, text: str) -> None:
        if self._gate.is_current(request_id):
            self.busy = False
            self.message.setText(text)

    def _show(self, rows: list[list[int]]) -> None:
        self._clear()
        for r, row in enumerate(rows):
            for c, idx in enumerate(row):
                pic = QLabel()
                img = self.cache.get(cache_key(self._hash, idx, self._zkey))
                pic.setPixmap(QPixmap.fromImage(img))
                self.grid.addWidget(pic, r, c)
        self.page_changed.emit(self.index)

    def _clear(self) -> None:
        while (item := self.grid.takeAt(0)) is not None:
            if item.widget():
                item.widget().deleteLater()
