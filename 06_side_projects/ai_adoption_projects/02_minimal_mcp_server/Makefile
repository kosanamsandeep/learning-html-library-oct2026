.PHONY: install run-docs run-examples test-docs test-examples clean

install:
	pip install "mcp[cli]" httpx

run-docs:
	python server.py

run-examples:
	python examples_server.py

test-docs:
	python test_client.py --server server.py

test-examples:
	python test_client.py --server examples_server.py

test-all: test-docs test-examples

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
