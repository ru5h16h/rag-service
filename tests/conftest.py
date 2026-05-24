from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def sample_text() -> str:
    return (
        "This is a sample document for testing. "
        "It contains multiple sentences with meaningful content. "
        "The quick brown fox jumps over the lazy dog. "
        "Sphinx of black quartz, judge my vow."
    )


@pytest.fixture
def mock_qdrant_client() -> AsyncMock:
    client = AsyncMock()
    client.collection_exists.return_value = True
    client.scroll.return_value = ([], None)
    return client


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    client = AsyncMock()
    client.embeddings.create.return_value = AsyncMock(data=[AsyncMock(embedding=[0.1] * 1536)])
    return client
