# PyInstaller spec for a one-file Windows build of the GUI.
# Build from the repo root:  pyinstaller packaging/agenda-gui.spec
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = SPECPATH + "/.."

# agenda.catalog imports page modules by name and holidays loads countries lazily,
# so PyInstaller's static analysis would miss them.
hidden = collect_submodules("agenda") + collect_submodules("holidays")

a = Analysis(
    [ROOT + "/packaging/launch_gui.py"],
    pathex=[ROOT],
    datas=[
        # agenda/fonts.py looks in <package parent>/assets/fonts
        (ROOT + "/assets/fonts", "assets/fonts"),
        (ROOT + "/agenda/gui/icons", "agenda/gui/icons"),
        # holidays loads its translations (holidays/locale/<lang>/LC_MESSAGES/<CC>.mo) from next
        # to its own code; collect_submodules only packs the .py files.
        *collect_data_files("holidays"),
    ],
    hiddenimports=hidden,
    excludes=["tkinter", "pytest"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="AgendaGenerator",
    console=False,
    upx=False,
)
