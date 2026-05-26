from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings
from src.storage.qdrant_client import ensure_collection

_VECTOR_SIZES = {
    "local": 768,
    "openai": 1536,
}


def _default_vector_size() -> int:
    return _VECTOR_SIZES[settings.embedding_backend]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the configured Qdrant collection.")
    parser.add_argument(
        "--vector-size",
        type=int,
        default=_default_vector_size(),
        help="Embedding vector size for the collection. Defaults to the active backend size.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    await ensure_collection(args.vector_size)
    print(
        f"Collection '{settings.qdrant_collection}' is ready at {settings.qdrant_url} "
        f"with vector size {args.vector_size}."
    )


if __name__ == "__main__":
    asyncio.run(main())
