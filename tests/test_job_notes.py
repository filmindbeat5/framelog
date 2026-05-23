"""Tests for framelog.job_notes."""

import pytest
from framelog.job_notes import JobNote, JobNotesManager


@pytest.fixture()
def manager() -> JobNotesManager:
    return JobNotesManager()


# ---------------------------------------------------------------------------
# JobNote
# ---------------------------------------------------------------------------

def test_note_to_dict_has_required_keys():
    note = JobNote(author="alice", text="looks good")
    d = note.to_dict()
    assert {"author", "text", "created_at"} == d.keys()


def test_note_roundtrip_from_dict():
    note = JobNote(author="bob", text="re-render needed")
    restored = JobNote.from_dict(note.to_dict())
    assert restored.author == note.author
    assert restored.text == note.text
    assert restored.created_at == note.created_at


# ---------------------------------------------------------------------------
# JobNotesManager.add_note
# ---------------------------------------------------------------------------

def test_add_note_returns_note(manager):
    note = manager.add_note("job-1", "alice", "first pass done")
    assert isinstance(note, JobNote)
    assert note.text == "first pass done"


def test_add_note_empty_text_raises(manager):
    with pytest.raises(ValueError, match="empty"):
        manager.add_note("job-1", "alice", "   ")


def test_multiple_notes_preserved_in_order(manager):
    manager.add_note("job-2", "alice", "note A")
    manager.add_note("job-2", "bob", "note B")
    notes = manager.get_notes("job-2")
    assert len(notes) == 2
    assert notes[0].text == "note A"
    assert notes[1].text == "note B"


# ---------------------------------------------------------------------------
# JobNotesManager.get_notes
# ---------------------------------------------------------------------------

def test_get_notes_unknown_job_returns_empty(manager):
    assert manager.get_notes("nonexistent") == []


def test_get_notes_returns_copy(manager):
    manager.add_note("job-3", "alice", "check colour")
    notes = manager.get_notes("job-3")
    notes.clear()
    assert len(manager.get_notes("job-3")) == 1


# ---------------------------------------------------------------------------
# JobNotesManager.clear_notes
# ---------------------------------------------------------------------------

def test_clear_notes_returns_count(manager):
    manager.add_note("job-4", "alice", "a")
    manager.add_note("job-4", "alice", "b")
    assert manager.clear_notes("job-4") == 2
    assert manager.get_notes("job-4") == []


def test_clear_notes_unknown_job_returns_zero(manager):
    assert manager.clear_notes("ghost") == 0


# ---------------------------------------------------------------------------
# JobNotesManager.search_notes
# ---------------------------------------------------------------------------

def test_search_notes_case_insensitive(manager):
    manager.add_note("job-5", "alice", "Render FAILED due to OOM")
    manager.add_note("job-6", "bob", "all clear")
    results = manager.search_notes("failed")
    assert "job-5" in results
    assert "job-6" not in results


def test_search_notes_no_match_returns_empty(manager):
    manager.add_note("job-7", "alice", "everything nominal")
    assert manager.search_notes("crash") == {}


# ---------------------------------------------------------------------------
# JobNotesManager.all_job_ids_with_notes
# ---------------------------------------------------------------------------

def test_all_job_ids_sorted(manager):
    manager.add_note("job-z", "alice", "z")
    manager.add_note("job-a", "alice", "a")
    manager.add_note("job-m", "alice", "m")
    assert manager.all_job_ids_with_notes() == ["job-a", "job-m", "job-z"]


def test_all_job_ids_empty_when_no_notes(manager):
    assert manager.all_job_ids_with_notes() == []
