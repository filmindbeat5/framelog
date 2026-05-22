"""Tests for framelog.archive_index."""

import os

import pytest

from framelog.archive_index import (
    update_index,
    list_archives,
    find_archives_by_label,
    latest_archive,
    INDEX_FILENAME,
)


@pytest.fixture()
def archive_dir(tmp_path):
    return str(tmp_path)


def test_index_file_created_on_first_update(archive_dir):
    update_index(archive_dir, "/tmp/fake.json", 5, "nightly")
    assert os.path.isfile(os.path.join(archive_dir, INDEX_FILENAME))


def test_list_archives_empty_before_any_update(archive_dir):
    assert list_archives(archive_dir) == []


def test_list_archives_returns_entries(archive_dir):
    update_index(archive_dir, "/tmp/a1.json", 3, "daily")
    update_index(archive_dir, "/tmp/a2.json", 7, "weekly")
    entries = list_archives(archive_dir)
    assert len(entries) == 2


def test_entry_fields(archive_dir):
    update_index(archive_dir, "/tmp/test.json", 10, "test-label")
    entry = list_archives(archive_dir)[0]
    assert entry["filename"] == "test.json"
    assert entry["path"] == "/tmp/test.json"
    assert entry["label"] == "test-label"
    assert entry["job_count"] == 10
    assert "created_at" in entry


def test_find_archives_by_label_match(archive_dir):
    update_index(archive_dir, "/tmp/a.json", 2, "nightly")
    update_index(archive_dir, "/tmp/b.json", 4, "weekly")
    results = find_archives_by_label(archive_dir, "nightly")
    assert len(results) == 1
    assert results[0]["label"] == "nightly"


def test_find_archives_by_label_no_match(archive_dir):
    update_index(archive_dir, "/tmp/a.json", 2, "nightly")
    assert find_archives_by_label(archive_dir, "missing") == []


def test_latest_archive_none_when_empty(archive_dir):
    assert latest_archive(archive_dir) is None


def test_latest_archive_returns_most_recent(archive_dir):
    update_index(archive_dir, "/tmp/old.json", 1, "old")
    update_index(archive_dir, "/tmp/new.json", 2, "new")
    latest = latest_archive(archive_dir)
    assert latest["label"] == "new"


def test_multiple_updates_accumulate(archive_dir):
    for i in range(5):
        update_index(archive_dir, f"/tmp/job_{i}.json", i, "batch")
    assert len(list_archives(archive_dir)) == 5
