from __future__ import annotations

import logging
from dataclasses import dataclass

import spacy
import tiktoken
from spacy.language import Language

from src.chunking.base import BaseChunker, Chunk
from src.config import settings
from src.loaders.base import Document

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _SentenceSlice:
    text: str
    start_char: int
    end_char: int
    token_count: int


class SemanticChunker(BaseChunker):
    def __init__(self) -> None:
        self.nlp = self._load_nlp()
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = settings.chunk_size_tokens
        self.overlap = int(self.chunk_size * settings.chunk_overlap_pct)

    def _load_nlp(self) -> Language:
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy model 'en_core_web_sm' is not installed; falling back to sentencizer"
            )
            nlp = spacy.blank("en")
            nlp.add_pipe("sentencizer")
            return nlp

    def chunk(self, doc: Document, doc_id: str) -> list[Chunk]:
        if not doc.content.strip():
            return []

        sentences = self._sentence_slices(doc)
        if not sentences:
            return []

        chunks: list[Chunk] = []
        start_idx = 0

        while start_idx < len(sentences):
            end_idx = self._find_chunk_end(sentences, start_idx)
            chunk = self._build_chunk(doc, doc_id, len(chunks), sentences[start_idx:end_idx])
            chunks.append(chunk)

            if end_idx >= len(sentences):
                break

            next_start = self._compute_overlap_start(sentences, start_idx, end_idx)
            start_idx = end_idx if next_start <= start_idx else next_start

        return chunks

    def _sentence_slices(self, doc: Document) -> list[_SentenceSlice]:
        parsed = self.nlp(doc.content)
        sentences: list[_SentenceSlice] = []
        for span in parsed.sents:
            sentence_text = span.text.strip()
            if not sentence_text:
                continue

            raw_text = span.text
            leading = len(raw_text) - len(raw_text.lstrip())
            trailing = len(raw_text) - len(raw_text.rstrip())
            start_char = span.start_char + leading
            end_char = span.end_char - trailing
            token_count = len(self.enc.encode(sentence_text))
            sentences.append(
                _SentenceSlice(
                    text=sentence_text,
                    start_char=start_char,
                    end_char=end_char,
                    token_count=token_count,
                )
            )
        return sentences

    def _find_chunk_end(self, sentences: list[_SentenceSlice], start_idx: int) -> int:
        token_total = 0
        end_idx = start_idx
        while end_idx < len(sentences):
            sentence = sentences[end_idx]
            if end_idx > start_idx and token_total + sentence.token_count > self.chunk_size:
                break
            token_total += sentence.token_count
            end_idx += 1
            if token_total >= self.chunk_size:
                break
        return end_idx

    def _compute_overlap_start(
        self,
        sentences: list[_SentenceSlice],
        start_idx: int,
        end_idx: int,
    ) -> int:
        if self.overlap <= 0:
            return end_idx

        overlap_tokens = 0
        overlap_start = end_idx
        while overlap_start > start_idx and overlap_tokens < self.overlap:
            overlap_start -= 1
            overlap_tokens += sentences[overlap_start].token_count

        if end_idx - start_idx == 1 and overlap_start == start_idx:
            return end_idx

        return overlap_start

    def _build_chunk(
        self,
        doc: Document,
        doc_id: str,
        chunk_index: int,
        sentences: list[_SentenceSlice],
    ) -> Chunk:
        start_char = sentences[0].start_char
        end_char = sentences[-1].end_char
        return Chunk(
            text=doc.content[start_char:end_char],
            doc_id=doc_id,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
            metadata={**doc.metadata, "chunk_strategy": "semantic"},
        )
