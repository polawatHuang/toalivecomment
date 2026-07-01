import csv

from fbcollector.services.export.csv_writer import CsvWriterService


def test_write_raw_comments_has_utf8_bom_and_headers(tmp_path, repos, sample_comments):
    repos.comments.insert_batch(sample_comments)
    writer = CsvWriterService(repos, output_dir=tmp_path)

    path = writer.write_raw_comments()

    raw_bytes = path.read_bytes()
    assert raw_bytes.startswith(b"\xef\xbb\xbf")  # utf-8-sig BOM

    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["Timestamp", "Username", "Comment", "EmployeeID"]
    assert len(rows) == 1 + len(sample_comments)


def test_write_unique_users_and_employee_ids(tmp_path, repos, sample_comments):
    repos.comments.insert_batch(sample_comments)
    for comment in sample_comments:
        repos.users.upsert_on_comment(comment.username, comment.timestamp)

    writer = CsvWriterService(repos, output_dir=tmp_path)
    users_path = writer.write_unique_users()

    with open(users_path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["Username", "First Comment Time", "Comment Count"]


def test_atomic_write_leaves_no_temp_file(tmp_path, repos, sample_comments):
    repos.comments.insert_batch(sample_comments)
    writer = CsvWriterService(repos, output_dir=tmp_path)
    writer.write_raw_comments()

    leftover_temps = list(tmp_path.glob(".*.tmp"))
    assert leftover_temps == []


def test_mark_dirty_and_clear(repos, tmp_path):
    writer = CsvWriterService(repos, output_dir=tmp_path)
    assert not writer._dirty.is_set()
    writer.mark_dirty()
    assert writer._dirty.is_set()
