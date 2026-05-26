from __future__ import annotations

import tiktoken

from src.chunking.base import BaseChunker, Chunk
from src.config import settings
from src.loaders.base import Document


class FixedSizeChunker(BaseChunker):
    def __init__(self) -> None:
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = settings.chunk_size_tokens
        self.overlap = int(self.chunk_size * settings.chunk_overlap_pct)

    def chunk(self, doc: Document, doc_id: str) -> list[Chunk]:
        tokens = self.enc.encode(doc.content)
        if not tokens:
            return []

        step = self.chunk_size - self.overlap
        if step <= 0:
            msg = "chunk_overlap_pct must produce a positive chunk step"
            raise ValueError(msg)

        chunks: list[Chunk] = []
        for index, start in enumerate(range(0, len(tokens), step)):
            token_slice = tokens[start : start + self.chunk_size]
            text = self.enc.decode(token_slice)
            char_start = len(self.enc.decode(tokens[:start]))
            char_end = char_start + len(text)
            chunks.append(
                Chunk(
                    text=text,
                    doc_id=doc_id,
                    chunk_index=index,
                    start_char=char_start,
                    end_char=char_end,
                    metadata={**doc.metadata, "chunk_strategy": "fixed"},
                )
            )
            if start + self.chunk_size >= len(tokens):
                break

        return chunks
