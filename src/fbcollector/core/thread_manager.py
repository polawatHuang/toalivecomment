"""Lifecycle management for all worker threads: start/stop/join, never a bare ``kill()``."""

import threading

from fbcollector.utils.logger import get_logger

_log = get_logger("thread_manager")

_JOIN_TIMEOUT_SECONDS = 5.0


class StoppableThread(threading.Thread):
    """Protocol-ish base: any thread managed by ``ThreadManager`` must expose ``stop()``."""

    def stop(self) -> None:  # pragma: no cover - interface method
        raise NotImplementedError


class ThreadManager:
    """Owns the lifecycle of every background worker thread in the app."""

    def __init__(self) -> None:
        self._threads: dict[str, threading.Thread] = {}

    def register(self, name: str, thread: threading.Thread) -> None:
        self._threads[name] = thread

    def start_all(self) -> None:
        for name, thread in self._threads.items():
            if not thread.is_alive():
                thread.start()
                _log.info("Started thread: %s", name)

    def is_alive(self, name: str) -> bool:
        thread = self._threads.get(name)
        return thread is not None and thread.is_alive()

    def stop_all(self, timeout: float = _JOIN_TIMEOUT_SECONDS) -> None:
        for name, thread in self._threads.items():
            stop = getattr(thread, "stop", None)
            if callable(stop):
                stop()
        for name, thread in self._threads.items():
            if thread.is_alive():
                thread.join(timeout=timeout)
                if thread.is_alive():
                    _log.warning("Thread %s did not stop within %.1fs", name, timeout)
        self._threads.clear()
