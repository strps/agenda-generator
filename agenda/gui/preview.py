"""Preview widget: single, spread and sheet modes rasterised with pypdfium2 (synchronous)."""

import pypdfium2 as pdfium
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
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
from agenda.exporter import render_pages
from agenda.gui import preview_model as M


def rasterise(pdf_bytes: bytes, scale: float) -> list[QImage]:
    """Every page of ``pdf_bytes`` as a QImage at ``scale`` (1.0 = 72 dpi)."""
    doc = pdfium.PdfDocument(pdf_bytes)
    try:
        images = []
        for i in range(len(doc)):
            bmp = doc[i].render(scale=scale)
            img = QImage(bmp.buffer, bmp.width, bmp.height, bmp.stride, QImage.Format.Format_BGR888)
            images.append(img.copy())  # detach from the pdfium buffer
        return images
    finally:
        doc.close()


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

        bar = QHBoxLayout()
        self.prev_button = QPushButton("◀")
        self.next_button = QPushButton("▶")
        self.label = QLabel("")
        bar.addWidget(self.prev_button)
        bar.addWidget(self.label, 1)
        self.mode_buttons: dict[str, QPushButton] = {}
        group = QButtonGroup(self)
        group.setExclusive(True)
        for m in M.MODES:
            b = QPushButton(m.capitalize())
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
        self.message.setText(text)
        self._clear()
        self.label.setText("")

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
        pdf = render_pages(self.cfg, self.plan, M.render_indices(rows))
        doc = pdfium.PdfDocument(pdf)
        try:
            w, h = doc[0].get_size()
        finally:
            doc.close()
        cols = max(len(r) for r in rows)
        view = self.scroll.viewport()
        scale = M.zoom_scale(self.zoom, (w, h), len(rows), cols, (view.width(), view.height()))
        images = rasterise(pdf, scale)
        self._clear()
        for r, row in enumerate(rows):
            for c, idx in enumerate(row):
                pic = QLabel()
                pic.setPixmap(QPixmap.fromImage(images[M.pdf_position(rows, idx)]))
                self.grid.addWidget(pic, r, c)
        self.page_changed.emit(self.index)

    def _clear(self) -> None:
        while (item := self.grid.takeAt(0)) is not None:
            if item.widget():
                item.widget().deleteLater()
