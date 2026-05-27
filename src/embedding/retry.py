from __future__ import annotations

import logging
from collections.abc import Sequence

from tenacity import before_sleep_log, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class _MissingOpenAIRetryableError(Exception):
    """Fallback used only when the optional OpenAI package is not installed."""


def _load_openai_retryable_exceptions() -> tuple[type[BaseException], ...]:
    try:
        import openai
    except ImportError:
        return (_MissingOpenAIRetryableError,)

    retryable: Sequence[type[BaseException]] = (
        openai.RateLimitError,
        openai.APIConnectionError,
        openai.APITimeoutError,
    )
    return tuple(retryable)


RETRYABLE_OPENAI_EXCEPTIONS = _load_openai_retryable_exceptions()

RETRY_POLICY: dict[str, object] = {
    "retry": retry_if_exception_type(RETRYABLE_OPENAI_EXCEPTIONS),
    "stop": stop_after_attempt(5),
    "wait": wait_exponential(multiplier=1, min=1, max=60),
    "before_sleep": before_sleep_log(logger, logging.WARNING),
    "reraise": True,
}
