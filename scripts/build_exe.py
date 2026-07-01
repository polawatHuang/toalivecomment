"""Builds the single-file Windows EXE via PyInstaller.

Usage: python scripts/build_exe.py
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "packaging" / "fbcollector.spec"
ICON_PATH = REPO_ROOT / "assets" / "icons" / "app.ico"


def main() -> int:
    if not ICON_PATH.exists():
        print("Icon not found, generating placeholder assets first...")
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from generate_assets import generate

        generate()

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(SPEC_PATH)],
        cwd=REPO_ROOT,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
