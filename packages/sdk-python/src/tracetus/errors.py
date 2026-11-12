"""What a failed call gives back.

A refusal is a value here, not an exception, exactly as in the JavaScript
client: :func:`tracetus.outcome` turns any answer into ``data``, ``error`` and
the raw response. The code is what a caller should branch on — the API's own
when it answered, and one of this package's when nothing did.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

#: Codes this package produces itself, when no usable answer arrived.
#:
#: ``ANSWER_UNREADABLE`` is the one that matters most: the API accepted the
#: request and the answer could not be read, so the request may have taken
#: effect. Read the resource, or retry with the same key to get the stored
#: answer.
TRANSPORT_ERROR_CODES: tuple[str, ...] = (
    "TIMEOUT",
    "CONNECTION_FAILED",
    "REDIRECTED",
    "ANSWER_UNREADABLE",
    "BAD_ANSWER",
    "OUTCOME_UNKNOWN",
)

REDIRECT_FLOOR = 300
REDIRECT_CEILING = 400

REQUEST_ID_HEADER = "x-request-id"
SERVER_ERROR_FLOOR = 500
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
#: The API's code for "an earlier attempt of this call has not answered yet".
IN_PROGRESS_CODE = "IDEMPOTENCY_KEY_IN_PROGRESS"
CONFLICT = 409
UNCERTAIN_WARNING = "; the request may have taken effect"


def is_uncertain_answer(status: int, method: str, in_contract: bool) -> bool:
    """Whether the request may already have taken effect, from the answer alone.

    A read that failed changed nothing, whatever answered it. A write is the
    question, and the answer depends on what came back:

    * **A refusal the API published** (``422``, ``409 DUPLICATE_RECORD``, ...)
      is a decision about the request. It wrote nothing, and says so.
    * **A ``5xx``** is the server saying it failed, not that it did nothing: a
      ``500`` can come from a commit that landed and an answer that did not,
      and a ``502`` or ``504`` from a gateway that never saw the answer.
    * **Anything outside the contract** did not come from a part of the stack
      that knows whether the write happened.

    Reporting those last two as certain is the dangerous direction: a caller
    that trusts it issues again under a *new* key and writes twice. An unknown
    method counts as unsafe for the same reason.
    """
    if method.upper() in SAFE_METHODS:
        return False
    return status >= SERVER_ERROR_FLOOR or not in_contract


@dataclass(frozen=True)
class ErrorIssue:
    field_name: str
    code: str
    detail: str


@dataclass(frozen=True)
class TraceTusError:
    #: The API's code when it answered; one of ``TRANSPORT_ERROR_CODES`` when it did not.
    code: str
    message: str
    #: HTTP status of the answer. Zero when no answer arrived.
    status: int = 0
    #: ``x-request-id`` of the answer: the one thing worth quoting in a support thread.
    request_id: str | None = None
    #: Seconds the API asked the client to wait, when it asked.
    retry_after_s: float | None = None
    #: What the API found wrong, field by field. Never the value it received.
    issues: list[ErrorIssue] = field(default_factory=list)
    #: True when the request may already have taken effect.
    uncertain: bool = False


def _issues_of(raw: Any) -> list[ErrorIssue]:
    if not isinstance(raw, list):
        return []
    found = []
    for entry in raw:
        if not isinstance(entry, Mapping):
            continue
        name, code, detail = entry.get("field"), entry.get("code"), entry.get("detail")
        if isinstance(name, str) and isinstance(code, str) and isinstance(detail, str):
            found.append(ErrorIssue(name, code, detail))
    return found


def is_redirect(status: int) -> bool:
    return REDIRECT_FLOOR <= status < REDIRECT_CEILING


def redirect_error(status: int, headers: Mapping[str, str]) -> TraceTusError:
    """The API answered a redirect, which this client does not follow.

    Following one would carry the API key and the body to whatever host the
    redirect names, and would answer `data` for a request the API never saw. It
    is certain: nothing was sent to the new address, so nothing can have taken
    effect. The JavaScript client says the same thing under the same code.
    """
    return TraceTusError(
        code="REDIRECTED",
        message=(
            f"the API answered {status}; this client does not follow redirects, because"
            " following one would carry the API key and the body to another host"
        ),
        status=status,
        request_id=headers.get(REQUEST_ID_HEADER),
        uncertain=False,
    )


def error_from_body(
    body: Any,
    status: int,
    headers: Mapping[str, str],
    retry_after_s: float | None = None,
    method: str = "",
) -> TraceTusError:
    """Reads the API's error body. An answer outside the contract is BAD_ANSWER.

    ``method`` decides whether the failure may have taken effect; left out, it
    counts as unsafe, which is the side that does not lose a write.
    """
    request_id = headers.get(REQUEST_ID_HEADER)
    found = body.get("error") if isinstance(body, Mapping) else None
    code = found.get("code") if isinstance(found, Mapping) else None
    message = found.get("message") if isinstance(found, Mapping) else None
    in_contract = isinstance(code, str) and isinstance(message, str)
    uncertain = is_uncertain_answer(status, method, in_contract)
    warning = UNCERTAIN_WARNING if uncertain else ""

    if not in_contract or not isinstance(code, str) or not isinstance(message, str):
        return TraceTusError(
            code="BAD_ANSWER",
            message=f"the API answered {status} outside the published contract{warning}",
            status=status,
            request_id=request_id,
            retry_after_s=retry_after_s,
            uncertain=uncertain,
        )

    if status == CONFLICT and code == IN_PROGRESS_CODE:
        # The attempts ran out while an earlier attempt of this same call was
        # still being served, exactly as the JavaScript client reports it: the
        # outcome is unknown, and the *same* key is what reads it.
        return TraceTusError(
            code="OUTCOME_UNKNOWN",
            message=(
                "an earlier attempt of this call is still being served; retry with the same"
                " Idempotency-Key to read its answer"
            ),
            status=status,
            request_id=request_id,
            retry_after_s=retry_after_s,
            uncertain=True,
        )

    return TraceTusError(
        code=code,
        message=f"{message}{warning}",
        status=status,
        request_id=request_id,
        retry_after_s=retry_after_s,
        issues=_issues_of(found.get("issues")) if isinstance(found, Mapping) else [],
        uncertain=uncertain,
    )
