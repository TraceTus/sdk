"""The retry, the timeout and the idempotency key, under every operation.

This is where "nothing per endpoint" is kept honest in Python: the behaviour
sits in an ``httpx`` transport, below the generated client, so every operation
the generator produces — and every operation it will produce — gets it without
a line of its own.

The idempotency key is injected only when the request does not already carry
one, and that is what makes a retry safe: a retry sends the *same* request,
key included, so the API answers the first answer instead of writing again.

Nothing is kept on the transport between requests: the state of one request
lives in one call of :meth:`RetryingTransport.handle_request`, so a client
shared between threads behaves. What has to outlive the call — the status and
the request id of the last answer, for when the generated parser refuses the
body — lives in a context variable, which is per thread and per task.

Both transports are here, synchronous and asynchronous, over one policy.
"""

from __future__ import annotations

import asyncio
import json
import random as random_module
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

import httpx

from tracetus.retry import RetryLimits, decide_retry, read_retry_after

IDEMPOTENCY_HEADER = "Idempotency-Key"
RETRY_AFTER_HEADER = "retry-after"
REQUEST_ID_HEADER = "x-request-id"

_Sent = tuple[httpx.Response | None, httpx.HTTPError | None]


@dataclass(frozen=True)
class LastAnswer:
    """What the last answer of this call said about itself."""

    status: int
    request_id: str | None


#: The last answer handed to the generated client, per thread and per task.
#:
#: The generated operation parses the answer *inside* its own call, so when the
#: parser refuses a body the exception is all the caller gets: the status and
#: the request id are gone, and those are the two things worth reporting. A
#: context variable keeps them for the call that is running without any state
#: shared between calls (`result.py` reads it).
LAST_ANSWER: ContextVar[LastAnswer | None] = ContextVar("tracetus_last_answer", default=None)


def _remember(response: httpx.Response) -> None:
    LAST_ANSWER.set(
        LastAnswer(status=response.status_code, request_id=response.headers.get(REQUEST_ID_HEADER))
    )


def code_of(response: httpx.Response) -> str | None:
    """The API's own error code in an answer, when it carries one.

    Read because one answer has to be told apart by its code rather than its
    status: a ``409 IDEMPOTENCY_KEY_IN_PROGRESS`` is retried, while every other
    ``409`` is a refusal. Reading the body here is safe — the answer is read and
    closed before any retry either way — and anything that is not the published
    envelope is simply no code.
    """
    try:
        body = json.loads(response.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, httpx.HTTPError):
        return None

    error = body.get("error") if isinstance(body, dict) else None
    code = error.get("code") if isinstance(error, dict) else None

    return code if isinstance(code, str) else None


def _decide(
    request: httpx.Request,
    response: httpx.Response | None,
    attempt: int,
    limits: RetryLimits,
    random: Callable[[], float],
) -> Any:
    """The policy's answer for this attempt, for either transport."""
    if response is None:
        return decide_retry(
            method=request.method,
            status=None,
            retry_after_s=None,
            attempt=attempt,
            limits=limits,
            random=random,
        )

    _remember(response)

    return decide_retry(
        method=request.method,
        status=response.status_code,
        retry_after_s=retry_after_of(response.headers),
        attempt=attempt,
        limits=limits,
        random=random,
        code=code_of(response),
    )


class RetryingTransport(httpx.BaseTransport):
    """Sends, and sends again while the policy says the answer may change."""

    def __init__(
        self,
        inner: httpx.BaseTransport,
        limits: RetryLimits | None = None,
        sleep: Callable[[float], None] = time.sleep,
        random: Callable[[], float] = random_module.random,
        new_idempotency_key: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._inner = inner
        self._limits = limits or RetryLimits()
        self._sleep = sleep
        self._random = random
        self._new_idempotency_key = new_idempotency_key

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        _ensure_idempotency_key(request, self._new_idempotency_key)

        attempt = 0
        while True:
            attempt += 1
            response, failure = self._send(request)
            decision = _decide(request, response, attempt, self._limits, self._random)

            if not decision.retry:
                if response is None:
                    raise failure if failure is not None else httpx.TransportError("no answer")
                return response

            # The answer being retried is read and closed before the next
            # attempt: an unclosed response holds its pooled connection, and a
            # client that retries would leak one per attempt.
            if response is not None:
                response.read()
                response.close()

            self._sleep(decision.wait_s)

    def _send(self, request: httpx.Request) -> _Sent:
        try:
            return self._inner.handle_request(request), None
        except httpx.HTTPError as error:
            return None, error

    def close(self) -> None:
        self._inner.close()


class AsyncRetryingTransport(httpx.AsyncBaseTransport):
    """The same policy, awaited.

    It exists because the generated package offers ``asyncio_detailed`` for
    every operation. Without it, an async call through a client built here
    raised ``AttributeError`` — the sync transport has no
    ``handle_async_request`` — and the obvious workaround, handing the async
    client a plain transport, would have lost every retry silently. The policy
    itself is shared: this class differs from the synchronous one in its
    ``await``s and nothing else.
    """

    def __init__(
        self,
        inner: httpx.AsyncBaseTransport,
        limits: RetryLimits | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        random: Callable[[], float] = random_module.random,
        new_idempotency_key: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._inner = inner
        self._limits = limits or RetryLimits()
        self._sleep = sleep
        self._random = random
        self._new_idempotency_key = new_idempotency_key

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        _ensure_idempotency_key(request, self._new_idempotency_key)

        attempt = 0
        while True:
            attempt += 1
            response, failure = await self._send(request)

            if response is not None:
                await response.aread()

            decision = _decide(request, response, attempt, self._limits, self._random)

            if not decision.retry:
                if response is None:
                    raise failure if failure is not None else httpx.TransportError("no answer")
                return response

            # Read above and closed here, before the next attempt: an unclosed
            # answer holds its pooled connection.
            if response is not None:
                await response.aclose()

            await self._sleep(decision.wait_s)

    async def _send(self, request: httpx.Request) -> _Sent:
        try:
            return await self._inner.handle_async_request(request), None
        except httpx.HTTPError as error:
            return None, error

    async def aclose(self) -> None:
        await self._inner.aclose()


def _ensure_idempotency_key(request: httpx.Request, new_key: Callable[[], str]) -> None:
    """Every POST carries one, and the same one on every attempt of this request."""
    if request.method.upper() != "POST":
        return
    if IDEMPOTENCY_HEADER in request.headers:
        return
    request.headers[IDEMPOTENCY_HEADER] = new_key()


def retry_after_of(headers: Any) -> float | None:
    """``Retry-After`` of an answer, in seconds, in either form HTTP allows."""
    try:
        return read_retry_after(headers.get(RETRY_AFTER_HEADER))
    except AttributeError:
        return None
