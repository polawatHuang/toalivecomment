# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Facebook Live Collector Pro (onedir Windows build).

Build with: pyinstaller --clean --noconfirm packaging/fbcollector.spec
(or simply: python scripts/build_exe.py)

Deliberately onedir, not onefile, despite the spec's "Single EXE" wording. Onefile
re-extracts its entire bundle (600+ files - numpy, PIL, Tcl/Tk, Playwright,
customtkinter) to a fresh %TEMP% folder on *every single launch*. On a machine with
endpoint security software that scans each extracted file synchronously, this measured
over 5 minutes per launch and still hadn't finished - a direct violation of the spec's
own "One-click operation" requirement. Onedir extracts once, at install time (via the
Inno Setup installer in installer.iss), then launches near-instantly on every run after.
The end user still gets a single installer .exe to double-click (see installer.iss);
only the *runtime* representation changed from one exe to an exe + a folder of
dependencies sitting next to it.

Two known frozen-build pitfalls this spec deliberately guards against:

1. customtkinter ships its own JSON theme files under its package directory. Without
   collecting them, the frozen app crashes on theme load (works fine in dev because the
   files are on disk next to the package). ``collect_data_files`` below handles this.
2. Playwright's Python package needs its internal Node driver present to make ANY call
   (including ``connect_over_cdp``) even though we never call ``chromium.launch()`` and
   therefore never need Playwright's own browser binaries. ``collect_all`` handles this.
"""

import os

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# SPECPATH is injected by PyInstaller into the spec's globals and always points at the
# directory containing this .spec file, regardless of the CWD `pyinstaller` was invoked
# from. A hand-rolled relative path like ".." breaks depending on invocation directory -
# that broke this exact build once already (fbcollector wasn't found/bundled at all,
# producing a frozen exe that failed at startup with ModuleNotFoundError: fbcollector).
REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821

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
    [],
    exclude_binaries=True,
    name="FBLiveCollectorPro",
    console=False,
    icon=f"{REPO_ROOT}/assets/icons/app.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="FBLiveCollectorPro",
)
