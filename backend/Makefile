ifeq (,$(wildcard .env))
$(error .env file is missing. Please create one based on .env.example)
endif

include .env

CHECK_DIRS := .

# --- QA ---

format-fix:
	uv run ruff format $(CHECK_DIRS) 
	uv run ruff check --select I --fix

lint-fix:
	uv run ruff check --fix

format-check:
	uv run ruff format --check $(CHECK_DIRS) 
	uv run ruff check -e
	uv run ruff check --select I -e

lint-check:
	uv run ruff check $(CHECK_DIRS)

# --- Event Listeners ---

start-job-listener:
	python run_job_event_listener.py

start-file-listener:
	python run_file_listener.py

start-notification-listener:
	python run_notification_event_listener.py

start-all-listeners:
	python run_all_event_listeners.py

# --- Services ---

start-api:
	python run_api_server.py

start-notification-websocket:
	python run_notification_websocket_service.py
