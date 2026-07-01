from datetime import datetime

from fbcollector.services.storage.models import RawComment


def test_user_repository_keeps_first_occurrence(repos):
    t1 = datetime(2026, 1, 1, 10, 0, 0)
    t2 = datetime(2026, 1, 1, 10, 5, 0)
    repos.users.upsert_on_comment("alice", t1)
    repos.users.upsert_on_comment("alice", t2)

    users = repos.users.all()
    assert len(users) == 1
    assert users[0].first_comment_time == t1
    assert users[0].comment_count == 2


def test_employee_repository_tracks_duplicate_count(repos):
    t1 = datetime(2026, 1, 1, 10, 0, 0)
    t2 = datetime(2026, 1, 1, 10, 5, 0)
    repos.employees.upsert_on_comment("1234", "alice", t1)
    repos.employees.upsert_on_comment("1234", "bob", t2)

    entries = repos.employees.all()
    assert len(entries) == 1
    assert entries[0].first_user == "alice"
    assert entries[0].first_time == t1
    assert entries[0].duplicate_count == 1


def test_comment_repository_insert_batch_and_count(repos, sample_comments):
    inserted = repos.comments.insert_batch(sample_comments)
    assert inserted == len(sample_comments)
    assert repos.comments.count() == len(sample_comments)


def test_comment_repository_ignores_duplicate_hash(repos, sample_comments):
    repos.comments.insert_batch(sample_comments)
    inserted_again = repos.comments.insert_batch(sample_comments)
    assert inserted_again == 0
    assert repos.comments.count() == len(sample_comments)


def test_comment_repository_fetch_page_newest_first(repos, sample_comments):
    repos.comments.insert_batch(sample_comments)
    page = repos.comments.fetch_page(0, 2)
    assert len(page) == 2
    assert page[0].hash == sample_comments[-1].hash


def test_comment_repository_search(repos, sample_comments):
    repos.comments.insert_batch(sample_comments)
    results = repos.comments.search("user1")
    assert all("user1" in r.username for r in results)
    assert len(results) > 0
