"""Application-wide constants. Single source of truth, no magic literals scattered elsewhere."""

from typing import Final

APP_NAME: Final[str] = "Facebook Live Collector Pro"
APP_EDITION: Final[str] = "Enterprise Edition"
APP_VERSION: Final[str] = "1.0.0"
APP_DIR_NAME: Final[str] = "FBLiveCollectorPro"

# Collector
DEFAULT_POLL_INTERVAL_MS: Final[int] = 300
DEFAULT_EMPLOYEE_ID_REGEX: Final[str] = r"\b\d{4,10}\b"
CHROME_DEBUG_PORT: Final[int] = 9222
CHROME_CDP_URL: Final[str] = f"http://localhost:{CHROME_DEBUG_PORT}"

# Storage
DB_FILENAME: Final[str] = "session.sqlite3"
WRITER_BATCH_MAX_ITEMS: Final[int] = 500
WRITER_BATCH_TIMEOUT_SECONDS: Final[float] = 0.25

# Export
DEFAULT_AUTOSAVE_INTERVAL_SECONDS: Final[int] = 5
RAW_COMMENTS_FILENAME: Final[str] = "RawComments.csv"
UNIQUE_USERS_FILENAME: Final[str] = "UniqueUsers.csv"
EMPLOYEE_IDS_FILENAME: Final[str] = "EmployeeIDs.csv"
WINNER_HISTORY_FILENAME: Final[str] = "WinnerHistory.csv"

# UI
UI_QUEUE_POLL_MS: Final[int] = 50
UI_QUEUE_MAX_EVENTS_PER_TICK: Final[int] = 200
LIVE_FEED_VISIBLE_ROW_POOL: Final[int] = 48
LIVE_FEED_IN_MEMORY_CACHE: Final[int] = 500
WHEEL_FRAME_INTERVAL_MS: Final[int] = 16
WHEEL_DEFAULT_DURATION_MS: Final[int] = 6000
WHEEL_MIN_FULL_ROTATIONS: Final[int] = 5

# Reconnect
RECONNECT_RETRY_DELAY_SECONDS: Final[float] = 2.0
RECONNECT_MAX_BACKOFF_SECONDS: Final[float] = 30.0
