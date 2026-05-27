"""Embedding backends and helpers."""

from src.embedding.base import EmbedderBase

__all__ = [
    "EmbedderBase",
    "LocalEmbedder",
    "OpenAIEmbedder",
    "embed_chunks",
]


def __getattr__(name: str) -> object:
    if name == "LocalEmbedder":
        from src.embedding.local_embedder import LocalEmbedder

        return LocalEmbedder
    if name == "OpenAIEmbedder":
        from src.embedding.openai_embedder import OpenAIEmbedder

        return OpenAIEmbedder
    if name == "embed_chunks":
        from src.embedding.batch_runner import embed_chunks

        return embed_chunks
    raise AttributeError(f"module 'src.embedding' has no attribute {name!r}")
