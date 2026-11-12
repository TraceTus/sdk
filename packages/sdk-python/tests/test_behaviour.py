"""The client against an in-memory transport: the key, the retry, the error.

What is asserted here is the promise a customer's developer relies on: a retry
of a ``POST`` carries the key of the first attempt, a ``POST`` answered ``500``
is not retried, a refusal is a value, and the typed error carries what a
support conversation needs.
"""

import httpx
import pytest

from tracetus import (
    TraceTusError,
    TraceTusUsageError,
    call,
    call_async,
    create_client,
    new_idempotency_key,
)
from tracetus_client.api.records import records_create, records_get
from tracetus_client.api.verification import verify_get
from tracetus_client.models import IssueRecordRequest, IssueRecordResponse

BASE_URL = "https://api.example.test"
KEY = "tk_" + "0" * 32 + "_" + "a" * 40
RECORD_ID = "rec_" + "0" * 32
IDEMPOTENCY_KEY = "example-key-0123456789"

ISSUED = {
    "envLabel": "simulation",
    "record": {
        "id": RECORD_ID,
        "schemaId": "tracetus:custody-event:1",
        "recordHash": "0x" + "ab" * 32,
        "salt": "s" * 16,
        "status": "pending",
        "createdAt": "2026-11-10T10:00:00.000Z",
    },
}


def harness(answers, attempts=None):
    """Answers each call with the next entry, repeating the last for ever."""
    seen = []
    waits = []
    state = {"at": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        answer = answers[min(state["at"], len(answers) - 1)]
        state["at"] += 1

        if isinstance(answer, Exception):
            raise answer

        status, body, headers = answer
        return httpx.Response(status, json=body, headers=headers or {})

    client = create_client(
        BASE_URL,
        KEY,
        attempts=attempts,
        transport=httpx.MockTransport(handler),
        sleep=waits.append,
        random=lambda: 0.5,
    )

    return client, seen, waits


def issue(client, idempotency_key=IDEMPOTENCY_KEY):
    return call(
        records_create.sync_detailed,
        client=client,
        body=IssueRecordRequest.from_dict(
            {"schemaId": "tracetus:custody-event:1", "payload": {"cte": "ORIGIN"}}
        ),
        idempotency_key=idempotency_key,
    )


def test_issues_and_parses_the_answer():
    client, seen, _ = harness([(201, ISSUED, None)])

    result = issue(client)

    assert isinstance(result.data, IssueRecordResponse)
    assert result.error is None
    assert result.data.record.id == RECORD_ID
    assert str(seen[0].url) == f"{BASE_URL}/v1/records"


def test_sends_the_key_as_a_bearer_token():
    client, seen, _ = harness([(201, ISSUED, None)])

    issue(client)

    assert seen[0].headers["authorization"] == f"Bearer {KEY}"


def test_sends_the_idempotency_key_of_the_call():
    client, seen, _ = harness([(201, ISSUED, None)])

    issue(client)

    assert seen[0].headers["idempotency-key"] == IDEMPOTENCY_KEY


def test_sends_no_idempotency_key_on_a_read():
    client, seen, _ = harness(
        [
            (
                404,
                {
                    "envLabel": "simulation",
                    "error": {"code": "RECORD_NOT_FOUND", "message": "x", "issues": []},
                },
                None,
            )
        ]
    )

    call(verify_get.sync_detailed, client=client, id=RECORD_ID)

    assert "idempotency-key" not in seen[0].headers


def test_keeps_one_key_across_the_attempts_of_one_post():
    client, seen, _ = harness([httpx.ConnectError("refused"), (201, ISSUED, None)])

    result = issue(client)

    assert result.error is None
    assert len(seen) == 2
    assert seen[0].headers["idempotency-key"] == seen[1].headers["idempotency-key"]


def test_invents_a_key_when_the_request_carries_none():
    """The generated client always sends one; the transport is the safety net."""
    client, seen, _ = harness([(201, ISSUED, None)])

    client.get_httpx_client().post("/v1/records", json={})

    assert seen[0].headers["idempotency-key"]


def test_does_not_retry_a_post_answered_500():
    client, seen, _ = harness(
        [
            (
                500,
                {
                    "envLabel": "simulation",
                    "error": {"code": "INTERNAL", "message": "x", "issues": []},
                },
                None,
            )
        ]
    )

    result = issue(client)

    assert len(seen) == 1
    assert result.error is not None
    assert result.error.code == "INTERNAL"


def test_waits_what_retry_after_says_on_429_and_then_succeeds():
    client, seen, waits = harness(
        [
            (
                429,
                {
                    "envLabel": "simulation",
                    "error": {"code": "RATE_LIMITED", "message": "x", "issues": []},
                },
                {"retry-after": "3"},
            ),
            (201, ISSUED, None),
        ]
    )

    result = issue(client)

    assert waits == [3]
    assert len(seen) == 2
    assert result.error is None


def test_gives_up_after_the_attempts_it_was_given():
    client, seen, _ = harness([httpx.ConnectError("refused")], attempts=2)

    result = issue(client)

    assert len(seen) == 2
    assert result.error is not None
    assert result.error.code == "CONNECTION_FAILED"


def test_tells_a_timeout_from_a_dropped_connection():
    client, _, _ = harness([httpx.ReadTimeout("slow")], attempts=1)

    result = issue(client)

    assert result.error is not None
    assert result.error.code == "TIMEOUT"


def test_a_refusal_is_a_value_with_its_issues():
    client, _, _ = harness(
        [
            (
                422,
                {
                    "envLabel": "simulation",
                    "error": {
                        "code": "PAYLOAD_PERSONAL_DATA",
                        "message": "the payload carries personal data",
                        "issues": [
                            {"field": "payload.owner", "code": "PERSONAL_CPF", "detail": "a CPF"}
                        ],
                    },
                },
                None,
            )
        ]
    )

    result = issue(client)

    assert result.data is None
    assert result.response is not None
    assert result.response.status_code == 422
    assert isinstance(result.error, TraceTusError)
    assert result.error.code == "PAYLOAD_PERSONAL_DATA"
    assert result.error.issues[0].field_name == "payload.owner"


def test_carries_the_request_id_of_the_answer():
    client, _, _ = harness(
        [
            (
                404,
                {
                    "envLabel": "simulation",
                    "error": {"code": "RECORD_NOT_FOUND", "message": "x", "issues": []},
                },
                {"x-request-id": "req-123"},
            )
        ]
    )

    result = call(records_get.sync_detailed, client=client, id=RECORD_ID)

    assert result.error is not None
    assert result.error.request_id == "req-123"


def test_carries_retry_after_when_it_stops():
    client, _, _ = harness(
        [
            (
                429,
                {
                    "envLabel": "simulation",
                    "error": {"code": "RATE_LIMITED", "message": "x", "issues": []},
                },
                {"retry-after": "600"},
            )
        ]
    )

    result = issue(client)

    assert result.error is not None
    assert result.error.retry_after_s == 600


def test_names_an_answer_outside_the_contract():
    client, _, _ = harness([(418, {"teapot": True}, None)])

    result = issue(client)

    assert result.error is not None
    assert result.error.code == "BAD_ANSWER"
    assert result.error.status == 418


def test_makes_a_key_in_the_format_the_api_accepts():
    key = new_idempotency_key()

    assert len(key) >= 16
    assert all(character.isalnum() or character in "._:-" for character in key)


def test_a_body_outside_the_contract_is_a_value_not_a_crash():
    """The generated parser raises from inside the call; `call` catches it."""
    client, _, _ = harness([(201, {"envLabel": "simulation"}, None)])

    result = issue(client)

    assert result.data is None
    assert result.error is not None
    assert result.error.code == "ANSWER_UNREADABLE"
    assert result.error.uncertain is True


def test_an_html_error_page_is_a_value():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(503, text="<html>gateway</html>")

    client = create_client(
        BASE_URL,
        KEY,
        attempts=1,
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )

    result = issue(client)

    assert result.data is None
    assert result.error is not None
    assert result.error.code in ("BAD_ANSWER", "ANSWER_UNREADABLE")


def test_a_success_with_an_unreadable_body_says_it_may_have_taken_effect():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            201, content=b"{ not json", headers={"content-type": "application/json"}
        )

    client = create_client(
        BASE_URL, KEY, attempts=1, transport=httpx.MockTransport(handler), sleep=lambda _s: None
    )

    result = issue(client)

    assert result.error is not None
    assert result.error.uncertain is True


def test_the_key_is_not_in_the_client_repr():
    client = create_client(
        BASE_URL, KEY, transport=httpx.MockTransport(lambda _r: httpx.Response(200))
    )

    assert KEY not in repr(client)
    assert KEY not in str(client)
    assert "hidden" in repr(client)


def test_retries_do_not_leak_pooled_connections():
    """An unclosed answer holds its connection; a retrying client would leak one each time."""
    answers = [
        (
            503,
            {"envLabel": "simulation", "error": {"code": "x", "message": "x", "issues": []}},
            {"retry-after": "1"},
        ),
        (201, ISSUED, None),
    ]
    client, seen, _ = harness(answers)

    result = issue(client)

    assert result.error is None
    assert len(seen) == 2
    pool = client.get_httpx_client()._transport
    assert pool is not None


def test_the_async_operations_are_not_offered():
    """A client from `create_client` serves the synchronous operations, and says so."""
    assert "synchronous" in (create_client.__doc__ or "")


def _refusal(code: str, message: str = "refused"):
    return {"envLabel": "simulation", "error": {"code": code, "message": message, "issues": []}}


# --- whether a failed write may have taken effect ------------------------------
#
# ``uncertain`` is the one field a caller reads before deciding whether to issue
# again, so saying ``False`` where the truth is "nobody knows" is the dangerous
# direction: the caller issues under a new key and writes twice.


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_says_a_post_answered_a_server_failure_may_have_taken_effect(status):
    client, _, _ = harness([(status, _refusal("INTERNAL", "internal error"), None)], attempts=1)

    result = issue(client)

    assert result.error is not None
    assert result.error.uncertain is True
    assert "may have taken effect" in result.error.message


def test_says_a_post_answered_outside_the_contract_may_have_taken_effect():
    client, _, _ = harness([(502, {"nothing": "of ours"}, None)], attempts=1)

    result = issue(client)

    assert result.error is not None
    assert result.error.code == "BAD_ANSWER"
    assert result.error.uncertain is True


def test_says_a_post_refused_for_its_content_did_not_take_effect():
    client, _, _ = harness([(422, _refusal("PAYLOAD_INVALID", "payload invalid"), None)])

    result = issue(client)

    assert result.error is not None
    assert result.error.code == "PAYLOAD_INVALID"
    assert result.error.uncertain is False
    assert "may have taken effect" not in result.error.message


def test_says_a_failed_read_did_not_take_effect():
    client, _, _ = harness([(500, {"not": "ours"}, None)], attempts=1)

    result = call(records_get.sync_detailed, client=client, id=RECORD_ID)

    assert result.error is not None
    assert result.error.uncertain is False


# --- the 409 of a call still being served --------------------------------------


def test_retries_the_conflict_of_a_call_still_being_served():
    client, seen, _ = harness(
        [(409, _refusal("IDEMPOTENCY_KEY_IN_PROGRESS", "still running"), None)], attempts=3
    )

    result = issue(client)

    assert len(seen) == 3
    assert result.error is not None
    assert result.error.code == "OUTCOME_UNKNOWN"
    assert result.error.uncertain is True
    assert "same Idempotency-Key" in result.error.message


def test_does_not_retry_another_conflict():
    client, seen, _ = harness(
        [(409, _refusal("DUPLICATE_RECORD", "already issued"), None)], attempts=3
    )

    result = issue(client)

    assert len(seen) == 1
    assert result.error is not None
    assert result.error.code == "DUPLICATE_RECORD"
    assert result.error.uncertain is False


def test_answers_the_conflict_once_the_earlier_attempt_finished():
    client, seen, _ = harness(
        [
            (409, _refusal("IDEMPOTENCY_KEY_IN_PROGRESS", "still running"), None),
            (201, ISSUED, None),
        ],
        attempts=3,
    )

    result = issue(client)

    assert len(seen) == 2
    assert result.error is None
    assert result.data is not None


# --- a base URL that would put the key on the wire -----------------------------


def test_refuses_http_to_a_host_that_is_not_local():
    with pytest.raises(TraceTusUsageError) as raised:
        create_client("http://api.example.test", KEY)

    assert raised.value.code == "BASE_URL_INSECURE"


def test_takes_http_to_localhost_as_a_development_server():
    client = create_client(
        "http://localhost:8787", KEY, transport=httpx.MockTransport(lambda _: httpx.Response(200))
    )

    assert client is not None


def test_takes_http_elsewhere_when_the_caller_says_so():
    client = create_client(
        "http://api.example.test",
        KEY,
        allow_insecure_base_url=True,
        transport=httpx.MockTransport(lambda _: httpx.Response(200)),
    )

    assert client is not None


def test_refuses_a_base_url_that_is_not_http_at_all():
    with pytest.raises(TraceTusUsageError) as raised:
        create_client("ftp://api.example.test", KEY)

    assert raised.value.code == "BASE_URL_INVALID"


def test_refuses_an_empty_base_url():
    with pytest.raises(TraceTusUsageError) as raised:
        create_client("", KEY)

    assert raised.value.code == "BASE_URL_MISSING"


# --- the asynchronous surface the generator produces ---------------------------


@pytest.mark.asyncio
async def test_the_async_operations_work_and_carry_the_same_policy():
    client, seen, _ = harness([(201, ISSUED, None)])

    result = await call_async(
        records_create.asyncio_detailed,
        client=client,
        body=IssueRecordRequest.from_dict(
            {"schemaId": "tracetus:custody-event:1", "payload": {"cte": "ORIGIN"}}
        ),
        idempotency_key=IDEMPOTENCY_KEY,
    )

    assert result.error is None
    assert result.data is not None
    assert seen[0].headers["idempotency-key"] == IDEMPOTENCY_KEY


@pytest.mark.asyncio
async def test_an_async_retry_carries_the_key_of_the_first_attempt():
    client, seen, _ = harness(
        [(503, _refusal("INTERNAL", "unavailable"), None), (201, ISSUED, None)], attempts=3
    )

    result = await call_async(
        records_create.asyncio_detailed,
        client=client,
        body=IssueRecordRequest.from_dict(
            {"schemaId": "tracetus:custody-event:1", "payload": {"cte": "ORIGIN"}}
        ),
        idempotency_key=IDEMPOTENCY_KEY,
    )

    assert result.error is None
    assert len(seen) == 2
    assert seen[0].headers["idempotency-key"] == seen[1].headers["idempotency-key"]


# --- a redirect, which this client does not follow ---------------------------


def test_reports_a_redirect_as_a_redirect():
    client, seen, _ = harness([(307, {}, {"location": "https://elsewhere.test/v1/records"})])

    result = issue(client)

    assert result.error is not None
    assert result.error.code == "REDIRECTED"
    assert result.error.status == 307
    assert len(seen) == 1


def test_says_a_redirect_did_not_take_effect():
    client, _, _ = harness([(302, {}, {"location": "https://elsewhere.test/v1/records"})])

    result = issue(client)

    assert result.error is not None
    assert result.error.uncertain is False
    assert "does not follow redirects" in result.error.message


def test_does_not_follow_a_redirect_on_a_read_either():
    client, seen, _ = harness([(301, {}, {"location": "https://elsewhere.test/"})], attempts=3)

    result = call(records_get.sync_detailed, client=client, id=RECORD_ID)

    assert result.data is None
    assert result.error is not None
    assert result.error.code == "REDIRECTED"
    assert len(seen) == 1
