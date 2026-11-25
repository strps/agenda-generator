"""Background full export through the core ``export_agenda`` (same path as the CLI)."""

from PySide6.QtCore import QObject, QRunnable, Signal

from agenda.config import Config
from agenda.cutreport import cut_report_lines, cut_status
from agenda.exporter import export_agenda
from agenda.textfit import CutLog


class ExportSignals(QObject):
    progress = Signal(int, int)  # pages done, total
    done = Signal(str, str, str)  # written path, cut status suffix, full cut report ('' = no cuts)
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
            cuts = CutLog()
            out = export_agenda(
                self.cfg, self.path, progress=self.signals.progress.emit, cuts=cuts, **kw
            )
            report = "\n".join(cut_report_lines(cuts)) if cuts else ""
            self.signals.done.emit(str(out), cut_status(cuts), report)
        except Exception as exc:  # noqa: BLE001 - reported to the user instead of killing the thread
            self.signals.failed.emit(str(exc))
