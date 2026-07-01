"""Launches and supervises a dedicated Chrome process with CDP remote debugging enabled.

The app manages its own Chrome instance (a separate, temporary profile) rather than
asking the user to relaunch their everyday Chrome with special flags. This avoids
"Chrome is already running with this profile" conflicts and keeps CONNECT a one-click
operation, per the spec's "no complicated setup" requirement.
"""

import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from fbcollector.constants import CHROME_CDP_URL, CHROME_DEBUG_PORT
from fbcollector.utils.logger import get_logger

_log = get_logger("chrome_manager")

_COMMON_WINDOWS_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


class ChromeNotFoundError(RuntimeError):
    """Raised when no Chrome executable can be located on this machine."""


class ChromeManager:
    """Launches/tracks/terminates a managed Chrome process for CDP attach."""

    def __init__(self, debug_port: int = CHROME_DEBUG_PORT) -> None:
        self._debug_port = debug_port
        self._process: subprocess.Popen | None = None
        self._user_data_dir = Path(tempfile.mkdtemp(prefix="fbcollector_chrome_profile_"))

    def find_chrome_executable(self) -> Path:
        which_result = shutil.which("chrome") or shutil.which("chrome.exe") or shutil.which("google-chrome")
        if which_result:
            return Path(which_result)
        for candidate in _COMMON_WINDOWS_PATHS:
            path = Path(candidate)
            if path.exists():
                return path
        raise ChromeNotFoundError(
            "Could not find a Google Chrome installation. Please install Chrome or add it to PATH."
        )

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def launch(self, start_url: str = "https://www.facebook.com") -> subprocess.Popen:
        if self.is_running():
            return self._process
        chrome_path = self.find_chrome_executable()
        self._process = subprocess.Popen(
            [
                str(chrome_path),
                f"--remote-debugging-port={self._debug_port}",
                f"--user-data-dir={self._user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                start_url,
            ]
        )
        _log.info("Launched managed Chrome (pid=%s) on debug port %d", self._process.pid, self._debug_port)
        return self._process

    def wait_until_debug_port_ready(self, timeout_seconds: float = 15.0) -> bool:
        deadline = time.monotonic() + timeout_seconds
        version_url = f"{CHROME_CDP_URL}/json/version"
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(version_url, timeout=1.0):  # noqa: S310 - localhost CDP only
                    return True
            except (urllib.error.URLError, OSError):
                time.sleep(0.3)
        return False

    def terminate(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None
        shutil.rmtree(self._user_data_dir, ignore_errors=True)
