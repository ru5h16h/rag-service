from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from src.loaders.base import BaseLoader, Document, build_base_metadata

_STRIP_TAGS = ["nav", "footer", "script", "style", "header"]


class HTMLLoader(BaseLoader):
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in {".html", ".htm"}

    def load(self, path: Path) -> list[Document]:
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")

        for element in soup.find_all(_STRIP_TAGS):
            element.decompose()

        root = soup.find("main") or soup.find("article") or soup.body or soup
        text = "\n".join(
            line for line in root.get_text("\n", strip=True).splitlines() if line
        ).strip()
        if not text:
            return []

        title = soup.title.string.strip() if soup.title and soup.title.string else None
        canonical_link = soup.find("link", rel="canonical")
        canonical_url = canonical_link.get("href") if canonical_link else None
        url = canonical_url or path.resolve().as_uri()

        metadata = build_base_metadata(path, file_format="html", title=title, url=url)
        return [Document(content=text, metadata=metadata)]
