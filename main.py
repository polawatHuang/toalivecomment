"""Entry point launcher for Facebook Live Collector Pro.

Kept as a thin shim so PyInstaller's Analysis has a single, stable script
entry point regardless of how the ``src`` package is organized.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from fbcollector.app import main  # noqa: E402

if __name__ == "__main__":
    main()
