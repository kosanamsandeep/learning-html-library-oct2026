---
name: pytest-tdd
description: |
  Use this skill when the user asks to add tests, write code TDD-style,
  or fix a failing pytest run in this repo. Provides our team's pytest
  conventions: AAA structure, parametrize over loops, integer cents
  for money. DO NOT use this skill for non-pytest test frameworks.
---

# pytest-tdd

When a user asks to add or fix tests in this repo, follow these rules.

## Workflow
1. Open `conftest.py` (if any) and reuse existing fixtures before
   adding new ones.
2. Use AAA — one test asserts one outcome. Comments labelling
   `# Arrange` / `# Act` / `# Assert` are encouraged.
3. Prefer `@pytest.mark.parametrize` over `for` loops in tests.
4. Money is integer cents — never floats. If you see a float in a
   test that touches money, fix the production code, not the test.
5. After writing tests, run `pytest -q` and iterate until green.

## File layout
- Tests live under `tests/` mirroring the `src/` path.
- One test file per source file (`src/orders.py` → `tests/test_orders.py`).

## Examples that should activate this skill
- "Add tests for `src/orders.py::compute_total`."
- "TDD a discount-code validator."
- "Why is `tests/test_orders.py::test_empty_cart` failing?"

## Guidelines
- Never edit production code without first writing a failing test
  that captures the intended behaviour.
- Use `tmp_path` for any filesystem touchpoint.
- If a test file does not exist yet, create it.
- Don't mock things you own — refactor the seam instead.
