"""Background rendering: a QRunnable that draws and rasterises pages off the GUI thread."""

import pypdfium2 as pdfium
from PySide6.QtCore import QObject, QRunnable, Signal
from PySide6.QtGui import QImage

from agenda.assembler import PagePlan
from agenda.config import Config
from agenda.exporter import render_pages
from agenda.gui import preview_model as M
from agenda.gui.render_cache import LatestGate


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


class RenderSignals(QObject):
    done = Signal(int, object)  # request id, {plan index: QImage}
    failed = Signal(int, str)


class RenderJob(QRunnable):
    """Render ``indices`` of ``plan`` at the scale ``zoom`` gives for ``grid`` = (rows, cols, avail_px)."""

    def __init__(
        self,
        request_id: int,
        gate: LatestGate,
        signals: RenderSignals,
        cfg: Config,
        plan: PagePlan,
        indices: list[int],
        zoom: str | int,
        grid: tuple[int, int, tuple[int, int]],
    ) -> None:
        super().__init__()
        self.request_id, self.gate, self.signals = request_id, gate, signals
        self.cfg, self.plan, self.indices, self.zoom, self.grid = cfg, plan, indices, zoom, grid

    def run(self) -> None:
        if not self.gate.is_current(self.request_id):
            return  # superseded while queued
        try:
            pdf = render_pages(self.cfg, self.plan, self.indices)
            doc = pdfium.PdfDocument(pdf)
            try:
                size = doc[0].get_size()
            finally:
                doc.close()
            rows, cols, avail = self.grid
            images = rasterise(pdf, M.zoom_scale(self.zoom, size, rows, cols, avail))
            self.signals.done.emit(self.request_id, dict(zip(self.indices, images, strict=True)))
        except Exception as exc:  # noqa: BLE001 - shown in the preview instead of crashing the thread
            self.signals.failed.emit(self.request_id, str(exc))
