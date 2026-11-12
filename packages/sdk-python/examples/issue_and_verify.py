"""Issue one record and verify its inclusion proof offline.

Runs against a local sandbox or any other installation; the integrator needs
the API URL and an issuer key::

    TRACETUS_API_URL=http://127.0.0.1:8787 TRACETUS_API_KEY=tk_... \\
    python examples/issue_and_verify.py

The proof exists once the worker seals the batch, so the script polls
``GET /v1/verify/{id}`` for a while. ``None`` at the end means the batch was
still open, not that the record is wrong.
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from tracetus import call, create_client, new_idempotency_key, verify_response_offline
from tracetus_client.api.records import records_create
from tracetus_client.api.verification import verify_get
from tracetus_client.models import IssueRecordRequest, IssueRecordResponse, VerifyResponse

DEFAULT_API_URL = "http://127.0.0.1:8787"
DEFAULT_SCHEMA_ID = "tracetus:custody-event:1"
DEFAULT_ATTEMPTS = 30
DEFAULT_INTERVAL_S = 2.0
# Rio Verde, Goiás: a locality code, never the name of a property.
PLACE_CODE = "BR-5218805"


class ExampleError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Outcome:
    env_label: str
    record_id: str
    record_hash: str
    proof_valid: bool | None
    attempts: int


def example_payload(occurred_at: datetime) -> dict[str, Any]:
    """A custody event of closed vocabulary only: stage, sub-type, when, lot, where."""
    stamp = occurred_at.astimezone(timezone.utc)
    return {
        "cte": "ORIGIN",
        "subType": "ORI.HARVEST",
        "occurredAt": stamp.isoformat().replace("+00:00", "Z"),
        "lotRef": f"lot-example-{int(stamp.timestamp())}",
        "placeCode": PLACE_CODE,
    }


def issue_and_verify(
    client: Any,
    schema_id: str = DEFAULT_SCHEMA_ID,
    attempts: int = DEFAULT_ATTEMPTS,
    interval_s: float = DEFAULT_INTERVAL_S,
    wait: Callable[[float], None] = time.sleep,
) -> Outcome:
    """Issue one record, wait for its proof, check the proof here."""
    issued = call(
        records_create.sync_detailed,
        client=client,
        body=IssueRecordRequest.from_dict(
            {"schemaId": schema_id, "payload": example_payload(datetime.now(timezone.utc))}
        ),
        # One key per issuance, kept across every retry of this call by the
        # transport, so a timeout issues once.
        idempotency_key=new_idempotency_key(),
    )
    if issued.error is not None or not isinstance(issued.data, IssueRecordResponse):
        code = issued.error.code if issued.error else "BAD_ANSWER"
        raise ExampleError("ISSUE_REFUSED", f"issue refused: {code}")

    record = issued.data.record
    last: VerifyResponse | None = None
    used = 0
    for attempt in range(1, attempts + 1):
        used = attempt
        verified = call(verify_get.sync_detailed, id=record.id, client=client)
        if verified.error is not None or not isinstance(verified.data, VerifyResponse):
            code = verified.error.code if verified.error else "BAD_ANSWER"
            raise ExampleError("VERIFY_REFUSED", f"verify refused: {code}")
        last = verified.data
        if last.proof is not None:
            break
        wait(interval_s)

    if last is None:
        raise ExampleError("VERIFY_REFUSED", "verify never answered")

    return Outcome(
        env_label=str(last.env_label.value),
        record_id=record.id,
        record_hash=record.record_hash,
        proof_valid=verify_response_offline(last),
        attempts=used,
    )


def read_options(environment: Mapping[str, str]) -> tuple[str, str]:
    api_key = environment.get("TRACETUS_API_KEY", "")
    if api_key == "":
        raise ExampleError("MISSING_KEY", "TRACETUS_API_KEY is required (an issuer key, tk_...)")
    return environment.get("TRACETUS_API_URL", DEFAULT_API_URL), api_key


def describe_outcome(outcome: Outcome) -> str:
    if outcome.proof_valid is None:
        proof = f"no proof yet after {outcome.attempts} polls: the batch is still open"
    else:
        state = "valid" if outcome.proof_valid else "INVALID"
        proof = f"proof {state} after {outcome.attempts} polls"
    return "\n".join(
        [
            f"environment: {outcome.env_label}",
            f"record: {outcome.record_id}",
            f"hash: {outcome.record_hash}",
            proof,
        ]
    )


def main() -> int:
    base_url, api_key = read_options(os.environ)
    outcome = issue_and_verify(create_client(base_url, api_key))
    sys.stdout.write(describe_outcome(outcome) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
