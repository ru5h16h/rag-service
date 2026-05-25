from __future__ import annotations

import re
from pathlib import Path

from src.loaders.base import BaseLoader, Document, build_base_metadata

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*(?:\n|$)", re.DOTALL)
_H1_RE = re.compile(r"(?m)^#\s+(.+?)\s*$")
_HEADING_PREFIX_RE = re.compile(r"^#{1,6}\s+")


class MarkdownLoader(BaseLoader):
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in {".md", ".markdown"}

    def load(self, path: Path) -> list[Document]:
        raw_content = path.read_text(encoding="utf-8")
        without_front_matter = _FRONT_MATTER_RE.sub("", raw_content, count=1)

        h1_match = _H1_RE.search(without_front_matter)
        h1_title = h1_match.group(1).strip() if h1_match else None

        cleaned_lines = [
            _HEADING_PREFIX_RE.sub("", line).strip() for line in without_front_matter.splitlines()
        ]
        text = "\n".join(line for line in cleaned_lines if line).strip()
        if not text:
            return []

        metadata = build_base_metadata(path, file_format="markdown", h1_title=h1_title)
        return [Document(content=text, metadata=metadata)]
