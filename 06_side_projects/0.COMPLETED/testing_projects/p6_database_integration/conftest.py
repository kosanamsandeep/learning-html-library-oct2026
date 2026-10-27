"""Fixture that gives each test a brand-new SQLite database on disk."""

import pytest

from repository import TodoRepository


@pytest.fixture
def repo(tmp_path):
    """Fresh database per test, cleaned up automatically by tmp_path."""
    db_file = tmp_path / "todos.sqlite"
    repository = TodoRepository(db_file)
    yield repository
    repository.close()
