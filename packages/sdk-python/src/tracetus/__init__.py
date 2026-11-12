"""TraceTus client for Python.

The request layer is ``tracetus_client``, generated from the OpenAPI document
the API publishes (``apps/api/openapi.json``); nothing there is written by hand
against a route, and ``scripts/generate.sh`` rewrites all of it.

This package adds the four things a generator cannot know:

- **A client with a credential and a timeout** (:func:`create_client`).
- **A retry that never issues twice.** One ``Idempotency-Key`` per ``POST``,
  kept across every attempt of that request; a ``POST`` answered ``500`` is not
  retried at all; ``429`` and ``503`` wait what ``Retry-After`` says, up to a
  ceiling (:mod:`tracetus.transport`, :mod:`tracetus.retry`).
- **A failed call as a value** (:func:`call`, or :func:`call_async` for the
  generated asynchronous operations), with the API's code, the HTTP status, the
  request id and ``Retry-After`` on a typed error, and ``uncertain`` saying
  whether the request may already have taken effect.
- **Offline verification** of an inclusion proof, which is the point of holding
  one (:func:`verify_response_offline`).
"""

from tracetus.client import (
    API_KEY_VARIABLE,
    DEFAULT_TIMEOUT_S,
    TraceTusUsageError,
    create_client,
    new_idempotency_key,
)
from tracetus.errors import TRANSPORT_ERROR_CODES, ErrorIssue, TraceTusError
from tracetus.proof import verify_proof_offline, verify_response_offline
from tracetus.result import Result, call, call_async
from tracetus.retry import (
    DEFAULT_ATTEMPTS,
    DEFAULT_MAX_RETRY_AFTER_S,
    RetryDecision,
    RetryLimits,
    decide_retry,
)
from tracetus.transport import AsyncRetryingTransport, RetryingTransport

__all__ = [
    "API_KEY_VARIABLE",
    "DEFAULT_ATTEMPTS",
    "DEFAULT_MAX_RETRY_AFTER_S",
    "DEFAULT_TIMEOUT_S",
    "TRANSPORT_ERROR_CODES",
    "AsyncRetryingTransport",
    "ErrorIssue",
    "Result",
    "RetryDecision",
    "RetryLimits",
    "RetryingTransport",
    "TraceTusError",
    "TraceTusUsageError",
    "call",
    "call_async",
    "create_client",
    "decide_retry",
    "new_idempotency_key",
    "verify_proof_offline",
    "verify_response_offline",
]
