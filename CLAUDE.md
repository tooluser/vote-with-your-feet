# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vote With Your Feet is a real-time polling application built with Flask and WebSockets. It has an admin interface for managing polls, a REST API for casting votes (A/B), and live display pages that update via Socket.IO.

## Commands

```bash
# Install dependencies
uv sync

# Run development server (localhost:8080)
uv run python app/main.py

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_models.py -v

# Run with Docker
docker-compose up

# Lint (uses Trunk)
trunk check
trunk fmt
```

## Architecture

**Backend**: Flask app factory pattern in `app/__init__.py` (`create_app()`). Entry point is `app/main.py` which also registers Socket.IO event handlers.

**Database**: SQLAlchemy with SQLite. Uses `scoped_session` managed via a global in `app/database.py` (`init_db()` / `get_session()`). Session cleanup happens in `teardown_appcontext`. Two models: `Poll` and `Vote` (defined in `app/models.py`).

**Routes**: Two blueprints:
- `app/routes/admin.py` — mounted at `/admin`, server-rendered HTML pages, protected by `@require_admin_secret` (query param `?secret=` or `X-Admin-Secret` header)
- `app/routes/api.py` — mounted at `/api`, JSON endpoints, vote endpoint protected by `@require_vote_password` (`X-Vote-Password` header)

**Real-time**: Flask-SocketIO emits `vote_cast` and `poll_activated` events. Display pages connect via Socket.IO client and refresh data on these events.

**Display pages** (defined as routes in `app/__init__.py`):
- `/display` — live results with vote counts
- `/display-no-votes` — poll options without counts
- `/display-completed` — grid of inactive polls with final results

**Templates/Static**: Jinja2 templates in `templates/`, CSS/JS in `static/`. Frontend is plain HTML/CSS/JS with Socket.IO client library.

## Testing

Tests use **pytest-describe** style (`def describe_...:` / `def it_...:` blocks). Each test file sets up its own in-memory SQLite database via fixtures. Tests that need the Flask app create a minimal app with only the needed blueprint registered, patching `db_module._session` directly.

## Configuration

Environment variables (or `.env` file): `ADMIN_SECRET`, `VOTE_PASSWORD`, `DATABASE_URL`, `SECRET_KEY`. Defaults are set in `app/config.py`. The API spec is documented in `openapi.yaml`.
