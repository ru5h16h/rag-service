from src.config import Settings


def test_settings_defaults(sample_text: str) -> None:
    settings = Settings()

    assert settings.embedding_backend == "local"
    assert settings.chunker_strategy == "fixed"
    assert "sample document" in sample_text
