"""The generated client against an in-memory httpx transport: the key travels as a
bearer token, the body is JSON, the error body is typed."""

import json

import httpx

from tracetus import create_client
from tracetus_client.api.records import records_create
from tracetus_client.api.verification import verify_get
from tracetus_client.models import ErrorResponse, IssueRecordRequest, IssueRecordResponse

BASE_URL = "https://api.example.test"
RECORD_ID = "rec_" + "0" * 32
HASH = "0x" + "ab" * 32
KEY = "tk_" + "0" * 32 + "_" + "a" * 40
IDEMPOTENCY_KEY = "example-key-0123456789"


def transport(status, body, seen):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler)


def test_sends_the_key_as_a_bearer_token_and_posts_json():
    seen = []
    answer = {
        "envLabel": "simulation",
        "record": {
            "id": RECORD_ID,
            "schemaId": "tracetus:custody-event:1",
            "recordHash": HASH,
            "salt": "s" * 16,
            "status": "pending",
            "createdAt": "2026-11-09T06:00:00.000Z",
        },
    }
    client = create_client(BASE_URL, KEY, transport=transport(201, answer, seen))
    body = IssueRecordRequest.from_dict(
        {"schemaId": "tracetus:custody-event:1", "payload": {"cte": "ORIGIN"}}
    )

    result = records_create.sync_detailed(client=client, body=body, idempotency_key=IDEMPOTENCY_KEY)

    assert isinstance(result.parsed, IssueRecordResponse)
    assert result.parsed.record.id == RECORD_ID
    assert seen[0].url == f"{BASE_URL}/v1/records"
    assert seen[0].headers["authorization"] == f"Bearer {KEY}"
    assert seen[0].headers["idempotency-key"] == IDEMPOTENCY_KEY
    assert json.loads(seen[0].content) == {
        "schemaId": "tracetus:custody-event:1",
        "payload": {"cte": "ORIGIN"},
    }


def test_verifies_without_a_key():
    seen = []
    answer = {
        "envLabel": "simulation",
        "proofValid": None,
        "record": {
            "id": RECORD_ID,
            "schemaId": "tracetus:custody-event:1",
            "recordHash": HASH,
            "status": "pending",
            "createdAt": "2026-11-09T06:00:00.000Z",
        },
        "issuer": {"legalName": "Emissor Exemplo Ltda", "city": None, "country": "BR"},
        "batch": None,
        "proof": None,
        "anchors": [],
    }
    client = create_client(BASE_URL, transport=transport(200, answer, seen))

    result = verify_get.sync_detailed(id=RECORD_ID, client=client)

    assert result.status_code == 200
    assert "authorization" not in seen[0].headers
    assert seen[0].url == f"{BASE_URL}/v1/verify/{RECORD_ID}"


def test_parses_the_typed_error_body_on_a_refusal():
    seen = []
    answer = {
        "envLabel": "simulation",
        "error": {
            "code": "PAYLOAD_PERSONAL_DATA",
            "message": "the payload carries personal data",
            "issues": [{"field": "kde.gtaNumber", "code": "PERSONAL_CPF", "detail": "x"}],
        },
    }
    client = create_client(BASE_URL, KEY, transport=transport(422, answer, seen))
    body = IssueRecordRequest.from_dict({"schemaId": "tracetus:custody-event:1", "payload": {}})

    result = records_create.sync_detailed(client=client, body=body, idempotency_key=IDEMPOTENCY_KEY)

    assert result.status_code == 422
    assert isinstance(result.parsed, ErrorResponse)
    assert result.parsed.error.code == "PAYLOAD_PERSONAL_DATA"
