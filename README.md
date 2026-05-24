# rag-api

Scaffold for a multi-tenant RAG API service with an offline ingestion pipeline.

## Development workflow

This project uses:

- `pyproject.toml` for package metadata, dependencies, and tool configuration
- `uv` for dependency resolution, installs, and command execution
- `nox` for lint and test orchestration

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
