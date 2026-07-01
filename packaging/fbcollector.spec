# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Facebook Live Collector Pro (onefile Windows build).

Build with: pyinstaller --clean --noconfirm packaging/fbcollector.spec
(or simply: python scripts/build_exe.py)

Two known frozen-build pitfalls this spec deliberately guards against:

1. customtkinter ships its own JSON theme files under its package directory. Without
   collecting them, the frozen app crashes on theme load (works fine in dev because the
   files are on disk next to the package). ``collect_data_files`` below handles this.
2. Playwright's Python package needs its internal Node driver present to make ANY call
   (including ``connect_over_cdp``) even though we never call ``chromium.launch()`` and
   therefore never need Playwright's own browser binaries. ``collect_all`` handles this.
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

REPO_ROOT = ".."

ctk_datas, ctk_binaries, ctk_hidden = collect_all("customtkinter")
pw_datas, pw_binaries, pw_hidden = collect_all("playwright")

datas = (
    [(f"{REPO_ROOT}/config", "config"), (f"{REPO_ROOT}/assets", "assets")]
    + ctk_datas
    + pw_datas
    + collect_data_files("PIL")
)
binaries = ctk_binaries + pw_binaries
hiddenimports = (
    ctk_hidden
    + pw_hidden
    + [
        "customtkinter",
        "PIL._tkinter_finder",
        "playwright.sync_api",
    ]
)

a = Analysis(
    [f"{REPO_ROOT}/main.py"],
    pathex=[REPO_ROOT, f"{REPO_ROOT}/src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="FBLiveCollectorPro",
    console=False,
    icon=f"{REPO_ROOT}/assets/icons/app.ico",
    onefile=True,
)
