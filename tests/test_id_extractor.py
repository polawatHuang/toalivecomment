import pytest

from fbcollector.utils.id_extractor import EmployeeIdExtractor, InvalidEmployeeIdRegexError


def test_default_regex_matches_within_bounds():
    extractor = EmployeeIdExtractor()
    assert extractor.extract("my id is 1234") == "1234"
    assert extractor.extract("id 0009988 here") == "0009988"
    assert extractor.extract("id 123456") == "123456"


def test_default_regex_rejects_too_short():
    extractor = EmployeeIdExtractor()
    assert extractor.extract("call 123 now") is None


def test_default_regex_rejects_too_long_run():
    extractor = EmployeeIdExtractor()
    # an 11-digit run has no valid 4-10 digit substring bounded by word boundaries
    assert extractor.extract("phone 12345678901 please") is None


def test_boundary_lengths():
    extractor = EmployeeIdExtractor()
    assert extractor.extract("exactly 1234567890 ten digits") == "1234567890"


def test_no_match_returns_none():
    extractor = EmployeeIdExtractor()
    assert extractor.extract("no digits here") is None


def test_custom_regex_override():
    extractor = EmployeeIdExtractor(pattern=r"EMP-\d{3}")
    assert extractor.extract("badge EMP-042 scanned") == "EMP-042"
    assert extractor.extract("badge 042 scanned") is None


def test_invalid_regex_raises():
    with pytest.raises(InvalidEmployeeIdRegexError):
        EmployeeIdExtractor(pattern="(unclosed")
