"""Background full export through the core ``export_agenda`` (same path as the CLI)."""

from PySide6.QtCore import QObject, QRunnable, Signal

from agenda.config import Config
from agenda.exporter import export_agenda


class ExportSignals(QObject):
    progress = Signal(int, int)  # pages done, total
    done = Signal(str)  # written path
    failed = Signal(str)


class ExportJob(QRunnable):
    def __init__(
        self,
        cfg: Config,
        path: str,
        signals: ExportSignals,
        pages: list[int] | None = None,
    ) -> None:
        super().__init__()
        self.cfg, self.path, self.signals, self.pages = cfg, path, signals, pages

    def run(self) -> None:
        try:
            kw = {"pages": self.pages} if self.pages else {}
            out = export_agenda(self.cfg, self.path, progress=self.signals.progress.emit, **kw)
            self.signals.done.emit(str(out))
        except Exception as exc:  # noqa: BLE001 - reported to the user instead of killing the thread
            self.signals.failed.emit(str(exc))
