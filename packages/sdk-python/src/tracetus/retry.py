"""When the client tries again, and how long it waits first.

The same policy as the JavaScript client, for the same reason: **a retry must
never issue twice**. Every ``POST`` carries one ``Idempotency-Key`` for all of
its attempts, so a retry after a timeout is answered with the first answer
instead of writing again. What that does not cover is an answer saying the
server failed in an unknown way: a ``500`` on a ``POST`` may or may not have
written, and the API deliberately refuses to replay such a key, so trying again
would only produce a ``409``. It is not retried.

Pure: the clock and the jitter come in as arguments, so the tests are exact.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

MILLISECONDS_IN_SECOND = 1000
TOO_MANY_REQUESTS = 429
SERVICE_UNAVAILABLE = 503
CONFLICT = 409
SERVER_ERROR_FLOOR = 500
BACKOFF_BASE = 2

#: The API's code for "an earlier attempt of this call has not answered yet".
IN_PROGRESS_CODE = "IDEMPOTENCY_KEY_IN_PROGRESS"

#: First wait of the backoff, in seconds; each attempt doubles it.
DEFAULT_BACKOFF_S = 0.25
#: Ceiling of one backoff wait, jitter applied inside it.
DEFAULT_MAX_BACKOFF_S = 8.0
#: Longest ``Retry-After`` the client will sit through on its own.
DEFAULT_MAX_RETRY_AFTER_S = 60.0
#: Attempts in total, the first one included.
DEFAULT_ATTEMPTS = 3

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


@dataclass(frozen=True)
class RetryLimits:
    attempts: int = DEFAULT_ATTEMPTS
    backoff_s: float = DEFAULT_BACKOFF_S
    max_backoff_s: float = DEFAULT_MAX_BACKOFF_S
    max_retry_after_s: float = DEFAULT_MAX_RETRY_AFTER_S


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    wait_s: float = 0.0


def _backoff_for(attempt: int, limits: RetryLimits, random: Callable[[], float]) -> float:
    grown = limits.backoff_s * (BACKOFF_BASE ** (attempt - 1))
    return min(grown, limits.max_backoff_s) * random()


def _wait_or_stop(
    retry_after_s: float | None,
    attempt: int,
    limits: RetryLimits,
    random: Callable[[], float],
) -> RetryDecision:
    if retry_after_s is None:
        return RetryDecision(True, _backoff_for(attempt, limits, random))
    if retry_after_s > limits.max_retry_after_s:
        return RetryDecision(False)
    return RetryDecision(True, retry_after_s)


def _is_in_progress(status: int | None, code: str | None) -> bool:
    """An earlier attempt of this very call is still being served."""
    return status == CONFLICT and code == IN_PROGRESS_CODE


def decide_retry(
    method: str,
    status: int | None,
    retry_after_s: float | None,
    attempt: int,
    limits: RetryLimits,
    random: Callable[[], float],
    code: str | None = None,
) -> RetryDecision:
    """Whether to send this request again, and how long to wait first.

    ``code`` is the API's own code when it answered one. It matters for exactly
    one answer: a ``409 IDEMPOTENCY_KEY_IN_PROGRESS`` means an earlier attempt
    of this same call is still being served, and waiting and asking again is
    the only way to learn its answer — so it is retried like a ``503`` rather
    than reported as a refusal.
    """
    if attempt >= limits.attempts:
        return RetryDecision(False)

    if status is None:
        return RetryDecision(True, _backoff_for(attempt, limits, random))

    if status in (TOO_MANY_REQUESTS, SERVICE_UNAVAILABLE) or _is_in_progress(status, code):
        return _wait_or_stop(retry_after_s, attempt, limits, random)

    if status >= SERVER_ERROR_FLOOR and method.upper() in SAFE_METHODS:
        return RetryDecision(True, _backoff_for(attempt, limits, random))

    return RetryDecision(False)


def read_retry_after(value: str | None) -> float | None:
    """``Retry-After`` in seconds. Anything that is not a count of seconds is None."""
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    return seconds if seconds >= 0 else None
