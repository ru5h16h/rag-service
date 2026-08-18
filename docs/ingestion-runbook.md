# Ingestion Runbook

How to ingest documents into Qdrant from a clean shell. Backing services:
Postgres runs locally (Homebrew `postgresql@18`); Qdrant is a hosted cloud
instance reached over its API. Connection details live in `.env`.

## 1. One-time setup

Start the local Postgres server and create the database named in `PG_DSN`
(default `rag`):

```bash
brew services start postgresql@18
createdb rag                       # skip if it already exists
```

Apply the database migrations (creates the `ingestion_jobs` table):

```bash
uv run alembic upgrade head
```

Verify the table exists:

```bash
psql rag -c "\dt"                  # expect: ingestion_jobs, alembic_version
```

> `en_core_web_sm` (spaCy) is only needed if `CHUNKER_STRATEGY=semantic`.
> The default is `fixed`, so this is optional:
> `uv run python -m spacy download en_core_web_sm`

## 2. Check Qdrant is reachable

Load `.env` into the shell first so `$QDRANT_URL` / `$QDRANT_API_KEY` are set:

```bash
set -a; source .env; set +a
```

The Qdrant REST API listens on port **6333** — include it in the URL for curl:

```bash
curl -sS "$QDRANT_URL:6333/collections" -H "api-key: $QDRANT_API_KEY" | jq
```

Or check through the same client the pipeline uses (most reliable):

```bash
uv run python -c "import asyncio; from src.storage.qdrant_client import get_client; print(asyncio.run(get_client().get_collections()))"
```

> Note: the Python client defaults to port 6333 automatically, so `QDRANT_URL`
> in `.env` stays portless. The `:6333` is only needed for raw curl.

## 3. Ingest documents

Put files (`.pdf`, `.html`, `.md`, `.docx`) anywhere under a directory, then
point the pipeline at it. Note the `run` subcommand:

```bash
uv run python -m src.pipeline.run run --path ./data/ --tenant dev
```

To reduce Prefect's per-task log noise, lower its log level for the run:

```bash
PREFECT_LOGGING_LEVEL=WARNING uv run python -m src.pipeline.run run --path ./data/ --tenant dev
```

Re-running is safe: content is deduplicated by SHA-256 hash, so already-indexed
chunks are skipped rather than re-embedded.

### Example: ingest a real corpus

```bash
git clone --depth 1 https://github.com/reactjs/react.dev data/react-docs
uv run python -m src.pipeline.run run --path ./data/react-docs/ --tenant dev
```

## 4. Confirm what landed

Point count in the Qdrant collection (should grow after each ingest):

```bash
curl -sS "$QDRANT_URL:6333/collections/$QDRANT_COLLECTION" -H "api-key: $QDRANT_API_KEY" | jq '.result.points_count'
```

Audit trail in Postgres:

```bash
psql rag -c "select source_path, status, chunk_count, skipped_count from ingestion_jobs order by created_at desc limit 10;"
```
