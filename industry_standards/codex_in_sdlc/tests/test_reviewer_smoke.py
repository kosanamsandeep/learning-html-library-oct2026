"""Smoke tests for ``src/reviewer.py``.

These exercise only the pure-Python helpers — they do not call the OpenAI
API or import ``openai-agents``. The live ``main()`` is covered by manual
runs and CI integration tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make ``src`` importable when running ``pytest`` from this folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reviewer import (  # noqa: E402
    _require_absolute,
    finish_review_impl,
    read_diff_impl,
)


def test_require_absolute_accepts_absolute_path(tmp_path: Path) -> None:
    # Arrange / Act
    result = _require_absolute(str(tmp_path))

    # Assert
    assert result == tmp_path


def test_require_absolute_rejects_relative_path() -> None:
    with pytest.raises(ValueError):
        _require_absolute("src/reviewer.py")


def test_read_diff_reads_file(tmp_path: Path) -> None:
    # Arrange
    diff_file = tmp_path / "patch.diff"
    diff_file.write_text(
        "--- a/x\n+++ b/x\n@@ -1 +1 @@\n-old\n+new\n", encoding="utf-8"
    )

    # Act
    body = read_diff_impl(str(diff_file))

    # Assert
    assert "-old" in body
    assert "+new" in body


def test_finish_review_wraps_comments() -> None:
    # Arrange
    comments = [
        {"line": 12, "tag": "BUG", "text": "off-by-one in loop bound"},
        {"line": 30, "tag": "NIT", "text": "rename foo -> total_cents"},
    ]

    # Act
    result = finish_review_impl(comments)

    # Assert
    assert result == {"comments": comments, "count": 2}
