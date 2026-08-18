# rag-api

Scaffold for a multi-tenant RAG API service with an offline ingestion pipeline.

## Development workflow

This project uses:

- `pyproject.toml` for package metadata, dependencies, and tool configuration
- `uv` for dependency resolution, installs, and command execution
- `nox` for lint and test orchestration

## Backing services

- **Qdrant** — a hosted/managed instance reached over its API. `QDRANT_URL` and
  `QDRANT_API_KEY` in `.env` point at that endpoint.
- **Postgres** — a locally installed server. `PG_DSN` in `.env` points at it.

Make sure the local Postgres service is running and the Qdrant API is reachable,
then apply migrations with `uv run alembic upgrade head` before running the pipeline.

Common commands:

```bash
uv sync --extra all
uv run pre-commit install
uv run python -m spacy download en_core_web_sm
uv run nox -s lint
uv run nox -s tests
uv run nox -s tests_integration
uv run python -m src.pipeline.run --help
```
