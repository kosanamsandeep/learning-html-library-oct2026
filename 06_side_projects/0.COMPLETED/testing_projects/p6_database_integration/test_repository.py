"""Integration tests — they actually hit SQLite, no mocks."""

import pytest


def test_add_returns_a_todo_with_id(repo):
    todo = repo.add("Write tests")

    assert todo.id > 0
    assert todo.title == "Write tests"
    assert todo.done is False


def test_added_todo_can_be_retrieved(repo):
    saved = repo.add("Buy milk")
    fetched = repo.get(saved.id)

    assert fetched == saved


def test_list_all_returns_items_in_insertion_order(repo):
    repo.add("first")
    repo.add("second")
    repo.add("third")

    titles = [t.title for t in repo.list_all()]
    assert titles == ["first", "second", "third"]


def test_mark_done_updates_only_the_target(repo):
    a = repo.add("a")
    b = repo.add("b")

    assert repo.mark_done(a.id) is True

    assert repo.get(a.id).done is True
    assert repo.get(b.id).done is False


def test_mark_done_on_missing_id_returns_false(repo):
    assert repo.mark_done(999) is False


def test_delete_removes_the_row(repo):
    todo = repo.add("temp")
    assert repo.delete(todo.id) is True
    assert repo.get(todo.id) is None


def test_delete_on_missing_id_returns_false(repo):
    assert repo.delete(123) is False


@pytest.mark.parametrize("bad_title", ["", "   ", "\n"])
def test_empty_title_is_rejected(repo, bad_title):
    with pytest.raises(ValueError):
        repo.add(bad_title)


def test_persistence_survives_repository_instance(tmp_path):
    """A separate test that verifies data is actually written to disk."""
    from repository import TodoRepository

    db_file = tmp_path / "persisted.sqlite"

    first = TodoRepository(db_file)
    first.add("survive me")
    first.close()

    second = TodoRepository(db_file)
    try:
        titles = [t.title for t in second.list_all()]
        assert titles == ["survive me"]
    finally:
        second.close()
