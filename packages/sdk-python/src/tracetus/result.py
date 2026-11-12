"""A failed call as a value, not an exception.

:func:`call` runs any operation of the generated client and answers ``data``,
``error`` and ``response`` — the same three the JavaScript client answers — so a
refusal by the API, a connection that never opened and an answer that cannot be
read are all read the same way and none of them interrupts the program.

It catches more than ``httpx`` raises, on purpose. The generated operation
parses the answer *inside* the call: a ``503`` carrying an HTML page, a ``201``
whose body is not the JSON it claims, an error envelope missing a field — each of
those raises from the parser, not from the transport, and each of them is a
failure a caller has to read rather than a crash.

It has nothing per endpoint: it takes the generated function and its arguments
and does the same thing for every operation there is.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

from tracetus.errors import TraceTusError, error_from_body, is_redirect, redirect_error
from tracetus.routes import method_of
from tracetus.transport import LAST_ANSWER, retry_after_of

SUCCESS_FLOOR = 200
SUCCESS_CEILING = 300

#: Failures that cannot have reached the API, so nothing can have taken effect.
#: Everything else a connection can do — a timeout, a reset, a dropped
#: connection — may have, and is reported as such.
_NEVER_SENT = (httpx.InvalidURL, httpx.UnsupportedProtocol)


@dataclass(frozen=True)
class Result:
    #: The parsed answer when the API accepted the call.
    data: Any | None
    #: The typed refusal, or this package's own code when no usable answer arrived.
    error: TraceTusError | None
    #: The answer as the generated client saw it. Absent when none arrived.
    response: Any | None


def _body_of(response: Any) -> Any:
    try:
        return json.loads(response.content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None


def _transport_code_of(failure: httpx.HTTPError) -> str:
    if isinstance(failure, httpx.TimeoutException):
        return "TIMEOUT"
    return "CONNECTION_FAILED"


def _failed(
    code: str,
    message: str,
    uncertain: bool = False,
    status: int = 0,
    request_id: str | None = None,
) -> Result:
    return Result(
        data=None,
        error=TraceTusError(
            code=code,
            message=message,
            uncertain=uncertain,
            status=status,
            request_id=request_id,
        ),
        response=None,
    )


def _method_of(operation: Callable[..., Any]) -> str:
    """The method of the operation being called, from the generated table."""
    return method_of(getattr(operation, "__module__", ""))


def _unreadable(failure: Exception) -> Result:
    """The generated parser refused the answer.

    The exception is raised *inside* the operation's own call, so the status and
    the request id would be lost with it; the transport remembers them for this
    call precisely so they are not. The request reached the API and may have
    taken effect: only our reading of the answer failed.
    """
    answer = LAST_ANSWER.get()

    return _failed(
        "ANSWER_UNREADABLE",
        f"the answer is outside the published contract ({type(failure).__name__});"
        " the request may have taken effect",
        uncertain=True,
        status=0 if answer is None else answer.status,
        request_id=None if answer is None else answer.request_id,
    )


def _failure(failure: httpx.HTTPError) -> Result:
    """A failure of the connection, told apart by whether anything was sent."""
    if isinstance(failure, _NEVER_SENT):
        return _failed(
            "CONNECTION_FAILED",
            f"the request was never sent ({type(failure).__name__})",
            uncertain=False,
        )

    return _failed(_transport_code_of(failure), type(failure).__name__, uncertain=True)


def call(operation: Callable[..., Any], **arguments: Any) -> Result:
    """Runs one operation of the generated client and reads its answer.

    ``operation`` is a ``sync_detailed`` of ``tracetus_client``, so the answer
    carries the status and the headers as well as the parsed body::

        from tracetus import call, create_client, new_idempotency_key
        from tracetus_client.api.records import records_create

        client = create_client("https://api.tracetus.com")
        result = call(
            records_create.sync_detailed,
            client=client,
            body=body,
            idempotency_key=new_idempotency_key(),
        )
    """
    LAST_ANSWER.set(None)

    try:
        response = operation(**arguments)
    except httpx.HTTPError as failure:
        return _failure(failure)
    except (KeyError, TypeError, ValueError) as failure:
        return _unreadable(failure)

    return _read(response, _method_of(operation))


async def call_async(operation: Callable[..., Any], **arguments: Any) -> Result:
    """The same, awaited: ``operation`` is an ``asyncio_detailed``.

    A client from :func:`tracetus.create_client` serves both surfaces — its
    asynchronous half carries the same retry policy — so this is the
    asynchronous twin of :func:`call` and nothing else::

        result = await call_async(
            records_create.asyncio_detailed,
            client=client,
            body=body,
            idempotency_key=new_idempotency_key(),
        )
    """
    LAST_ANSWER.set(None)

    try:
        response = await operation(**arguments)
    except httpx.HTTPError as failure:
        return _failure(failure)
    except (KeyError, TypeError, ValueError) as failure:
        return _unreadable(failure)

    return _read(response, _method_of(operation))


def _read(response: Any, method: str) -> Result:
    """One answer, read the same way for both surfaces."""
    if is_redirect(response.status_code):
        return Result(
            data=None,
            error=redirect_error(response.status_code, _headers_of(response)),
            response=response,
        )

    if SUCCESS_FLOOR <= response.status_code < SUCCESS_CEILING:
        if response.parsed is None:
            return Result(
                data=None,
                error=TraceTusError(
                    code="ANSWER_UNREADABLE",
                    message="the answer could not be read; the request may have taken effect",
                    status=response.status_code,
                    request_id=_headers_of(response).get("x-request-id"),
                    uncertain=True,
                ),
                response=response,
            )

        return Result(data=response.parsed, error=None, response=response)

    return Result(
        data=None,
        error=error_from_body(
            _body_of(response),
            response.status_code,
            _headers_of(response),
            retry_after_of(response.headers) if hasattr(response, "headers") else None,
            method=method,
        ),
        response=response,
    )


def _headers_of(response: Any) -> dict:
    headers = getattr(response, "headers", {})
    try:
        return {name.lower(): value for name, value in headers.items()}
    except AttributeError:
        return {}
