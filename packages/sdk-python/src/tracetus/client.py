"""Client factory over the generated package.

What it adds to the generated client is what a generator cannot know: the
credential, a timeout, and the transport that retries without ever issuing
twice (:mod:`tracetus.transport`). Everything else — the routes, the models,
the signatures — is generated from ``apps/api/openapi.json`` and never written
by hand.
"""

from __future__ import annotations

import os
import random as random_module
import time
import uuid
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

import httpx

from tracetus.retry import RetryLimits
from tracetus.transport import AsyncRetryingTransport, RetryingTransport
from tracetus_client import AuthenticatedClient, Client

API_KEY_VARIABLE = "TRACETUS_API_KEY"

#: One attempt's own patience. Generous: a batch of a thousand records is one call.
DEFAULT_TIMEOUT_S = 30.0

#: Hosts where ``http://`` is a development server rather than a mistake.
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})


class TraceTusUsageError(ValueError):
    """The calling code is wrong, which is the one thing this package raises for.

    It carries a literal ``code`` so a caller can branch on it, like every
    error of the JavaScript client.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _checked_base_url(base_url: str, allow_insecure: bool) -> str:
    """Refuses a base URL that would put the issuer key on the wire in clear.

    The same rule as the JavaScript client, for the same reason: ``http://`` to
    a host that is not local is readable by anything on the path, and an issuer
    key read once is an issuer impersonated until it is revoked. A development
    server on ``localhost`` is fine, and ``allow_insecure_base_url`` is there
    for the deliberate exception — a staging API inside a private network.
    """
    if not base_url:
        raise TraceTusUsageError("BASE_URL_MISSING", "the client needs a base_url")

    parsed = urlsplit(base_url)

    if parsed.scheme not in ("http", "https"):
        raise TraceTusUsageError(
            "BASE_URL_INVALID", f"base_url must be http or https, not {parsed.scheme or 'nothing'}"
        )

    host = parsed.hostname or ""

    if parsed.scheme == "http" and not allow_insecure and host not in LOCAL_HOSTS:
        raise TraceTusUsageError(
            "BASE_URL_INSECURE",
            f"base_url is http to {host}, which would send the API key in clear;"
            " use https, or pass allow_insecure_base_url=True",
        )

    return base_url


def new_idempotency_key() -> str:
    """A key for one ``POST``, in the format the API accepts."""
    return str(uuid.uuid4())


class _AsyncOverSamePolicy:
    """Gives a generated client an asynchronous half that retries like the other.

    The generated class builds its asynchronous client from the same
    ``httpx_args`` as its synchronous one, and those carry a *synchronous*
    transport: every ``asyncio_detailed`` call raised ``AttributeError``
    (``'RetryingTransport' object has no attribute 'handle_async_request'``),
    and handing the asynchronous client a plain transport instead would have
    lost every retry without saying so.

    So the generated construction is reused — it is what injects the credential
    — with the asynchronous transport put in place of the synchronous one for
    the length of that one call.
    """

    _async_transport: httpx.AsyncBaseTransport
    _httpx_args: dict
    _async_client: httpx.AsyncClient | None

    def get_async_httpx_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            synchronous = self._httpx_args.get("transport")
            self._httpx_args["transport"] = self._async_transport

            try:
                # type: ignore[misc] — this mixin is applied to two generated
                # classes, so `super()` has no single static base here; the one
                # it resolves to at run time is the generated client beside it.
                super().get_async_httpx_client()  # type: ignore[misc]
            finally:
                self._httpx_args["transport"] = synchronous

        built = self._async_client

        if built is None:
            raise TraceTusUsageError(
                "ASYNC_CLIENT_MISSING", "the generated client did not build an async client"
            )

        return built


class _PublicClient(_AsyncOverSamePolicy, Client):
    """No credential: the one route that needs none, plus the asynchronous half."""


class _GuardedClient(_AsyncOverSamePolicy, AuthenticatedClient):
    """An authenticated client that does not print its token.

    The generated class is an ``attrs`` class, so its ``repr`` prints every
    field — the issuer key included. One stray ``print(client)`` or one
    exception rendered with its locals would put a credential in a log, which
    this repository's security rules forbid outright. Overriding ``repr`` is the
    whole fix, and the token is still there for the client to send.
    """

    def __repr__(self) -> str:
        return f"TraceTusClient(base_url={self._base_url!r}, token=<hidden>)"

    __str__ = __repr__


def create_client(
    base_url: str,
    api_key: str | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    attempts: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    random: Callable[[], float] = random_module.random,
    transport: httpx.BaseTransport | None = None,
    allow_insecure_base_url: bool = False,
    **httpx_args: Any,
) -> AuthenticatedClient | Client:
    """A client for the API at ``base_url``, with retries and a timeout.

    With an issuer key (``tk_...``) the client sends ``Authorization: Bearer``
    on every call; without one it can only call ``GET /v1/verify/{id}``, the
    one route that needs no key. The key is read from ``TRACETUS_API_KEY`` when
    it is not given.

    ``transport`` is for a test: give it ``httpx.MockTransport`` and the retry
    policy still wraps it, so a test exercises the real behaviour.
    ``sleep`` and ``random`` are injected for the same reason.

    **Both surfaces work.** The generated package exposes ``sync_detailed`` and
    ``asyncio_detailed`` for every operation, and the client returned here
    carries the retry policy on both: the synchronous transport and the
    asynchronous one are the same policy, so an ``await`` neither fails nor
    quietly stops retrying. Use :func:`tracetus.call` for the first and
    :func:`tracetus.call_async` for the second.

    ``http://`` to a host that is not local is refused, because an issuer key
    on a plain connection is readable by anything on the path. Pass
    ``allow_insecure_base_url=True`` to say you meant it.
    """
    checked = _checked_base_url(base_url, allow_insecure_base_url)
    limits = RetryLimits() if attempts is None else RetryLimits(attempts=attempts)
    inner = transport if transport is not None else httpx.HTTPTransport()
    wrapped = RetryingTransport(
        inner,
        limits=limits,
        sleep=sleep,
        random=random,
        new_idempotency_key=new_idempotency_key,
    )
    arguments: dict = {"transport": wrapped, **httpx_args}
    token = api_key if api_key else os.environ.get(API_KEY_VARIABLE, "")
    timeout = httpx.Timeout(timeout_s)

    client: AuthenticatedClient | Client

    if not token:
        client = _PublicClient(base_url=checked, timeout=timeout, httpx_args=arguments)
    else:
        client = _GuardedClient(
            base_url=checked, token=token, timeout=timeout, httpx_args=arguments
        )

    client._async_transport = _async_transport_for(transport, limits, random)

    return client


def _async_transport_for(
    transport: httpx.BaseTransport | None,
    limits: RetryLimits,
    random: Callable[[], float],
) -> httpx.AsyncBaseTransport:
    """The asynchronous half of the policy, over the same inner transport.

    A test's ``httpx.MockTransport`` answers both surfaces, so it is reused as
    it is; anything else gets the real asynchronous transport underneath.
    """
    inner = transport if isinstance(transport, httpx.AsyncBaseTransport) else None

    return AsyncRetryingTransport(
        inner if inner is not None else httpx.AsyncHTTPTransport(),
        limits=limits,
        random=random,
        new_idempotency_key=new_idempotency_key,
    )
