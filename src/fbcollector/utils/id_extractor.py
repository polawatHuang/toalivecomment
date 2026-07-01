"""Employee ID extraction from raw comment text, via a configurable regex."""

import re

from fbcollector.constants import DEFAULT_EMPLOYEE_ID_REGEX


class InvalidEmployeeIdRegexError(ValueError):
    """Raised when a user-supplied regex fails to compile."""


class EmployeeIdExtractor:
    """Extracts the first employee-ID-looking token from a comment.

    Default pattern matches a standalone run of 4-10 digits (per spec: "Only digits,
    length 4-10"). The pattern is configurable from Settings so operators can adapt it
    to their own ID format without a code change.
    """

    def __init__(self, pattern: str = DEFAULT_EMPLOYEE_ID_REGEX) -> None:
        self._pattern_str = pattern
        try:
            self._compiled = re.compile(pattern)
        except re.error as exc:
            raise InvalidEmployeeIdRegexError(f"Invalid employee ID regex {pattern!r}: {exc}") from exc

    @property
    def pattern(self) -> str:
        return self._pattern_str

    def extract(self, text: str) -> str | None:
        """Return the first match, or None if the comment contains no employee ID."""
        match = self._compiled.search(text)
        return match.group(0) if match else None
