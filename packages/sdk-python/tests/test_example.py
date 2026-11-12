"""The example against an in-memory API: it issues, polls until the proof exists,
and checks the proof with the same Merkle rule as the core."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from issue_and_verify import (
    ExampleError,
    Outcome,
    describe_outcome,
    example_payload,
    issue_and_verify,
    read_options,
)

from tracetus import create_client
from tracetus.proof import hash_pair

BASE_URL = "https://api.example.test"
RECORD_ID = "rec_" + "0" * 32
RECORD_HASH = "0x" + "ab" * 32
SIBLING = "0x" + "cd" * 32
ROOT = hash_pair(RECORD_HASH, SIBLING)
KEY = "tk_" + "0" * 32 + "_" + "a" * 40

ISSUED = {
    "envLabel": "simulation",
    "record": {
        "id": RECORD_ID,
        "schemaId": "tracetus:custody-event:1",
        "recordHash": RECORD_HASH,
        "salt": "s" * 16,
        "status": "pending",
        "createdAt": "2026-11-10T10:00:00.000Z",
    },
}


def verify_body(with_proof: bool) -> dict:
    return {
        "envLabel": "simulation",
        "proofValid": True if with_proof else None,
        "record": {
            "id": RECORD_ID,
            "schemaId": "tracetus:custody-event:1",
            "recordHash": RECORD_HASH,
            "status": "batched" if with_proof else "pending",
            "createdAt": "2026-11-10T10:00:00.000Z",
        },
        "issuer": {"legalName": "Emissor Exemplo Ltda", "city": None, "country": "BR"},
        "batch": (
            {
                "id": "bat_" + "1" * 32,
                "merkleRoot": ROOT,
                "leafCount": 2,
                "status": "sealed",
                "sealedAt": None,
            }
            if with_proof
            else None
        ),
        "proof": {"leafIndex": 0, "siblings": [SIBLING], "root": ROOT} if with_proof else None,
        "anchors": [],
    }


def fake_api(pending_polls: int, issue_status: int = 201):
    """Answers the issue, then ``pending_polls`` verifies without proof, then one with."""
    seen = []
    polls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "POST":
            if issue_status == 201:
                return httpx.Response(201, json=ISSUED)
            return httpx.Response(
                issue_status,
                json={
                    "envLabel": "simulation",
                    "error": {"code": "SCHEMA_UNKNOWN", "message": "x", "issues": []},
                },
            )
        polls["count"] += 1
        return httpx.Response(200, json=verify_body(polls["count"] > pending_polls))

    return httpx.MockTransport(handler), seen


def no_wait(_seconds: float) -> None:
    return None


def test_issues_waits_for_the_proof_and_finds_it_valid():
    transport, seen = fake_api(2)
    client = create_client(BASE_URL, KEY, transport=transport)

    outcome = issue_and_verify(client, wait=no_wait)

    assert outcome == Outcome(
        env_label="simulation",
        record_id=RECORD_ID,
        record_hash=RECORD_HASH,
        proof_valid=True,
        attempts=3,
    )
    assert [request.method for request in seen] == ["POST", "GET", "GET", "GET"]


def test_returns_no_proof_when_the_batch_stays_open_for_every_attempt():
    transport, _seen = fake_api(100)
    client = create_client(BASE_URL, KEY, transport=transport)

    outcome = issue_and_verify(client, attempts=3, wait=no_wait)

    assert outcome.proof_valid is None
    assert outcome.attempts == 3


def test_surfaces_a_refused_issue_as_a_typed_error():
    transport, _seen = fake_api(0, issue_status=422)
    client = create_client(BASE_URL, KEY, transport=transport)

    with pytest.raises(ExampleError) as refused:
        issue_and_verify(client, wait=no_wait)

    assert refused.value.code == "ISSUE_REFUSED"


def test_sends_a_payload_made_only_of_closed_vocabulary():
    payload = example_payload(datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc))

    assert payload["cte"] == "ORIGIN"
    assert payload["subType"] == "ORI.HARVEST"
    assert payload["occurredAt"] == "2026-11-10T10:00:00Z"
    assert payload["lotRef"].startswith("lot-example-")
    assert payload["placeCode"] == "BR-5218805"


def test_defaults_the_url_to_the_local_sandbox():
    assert read_options({"TRACETUS_API_KEY": "tk_x"}) == ("http://127.0.0.1:8787", "tk_x")


def test_refuses_to_run_without_an_issuer_key():
    with pytest.raises(ExampleError):
        read_options({})


def test_describes_an_open_batch_and_a_valid_proof():
    open_batch = describe_outcome(Outcome("simulation", RECORD_ID, RECORD_HASH, None, 30))
    valid = describe_outcome(Outcome("testnet", RECORD_ID, RECORD_HASH, True, 2))

    assert "environment: simulation" in open_batch
    assert "batch is still open" in open_batch
    assert "proof valid after 2 polls" in valid
