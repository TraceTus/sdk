# tracetus

TraceTus client for Python: issue records, read proofs, and check an inclusion
proof without asking anybody.

```bash
pip install tracetus
```

Python 3.10 and up, on `httpx`. Types included.

## Use

```python
from tracetus import call, create_client, new_idempotency_key, verify_response_offline
from tracetus_client.api.records import records_create
from tracetus_client.api.verification import verify_get
from tracetus_client.models import IssueRecordRequest

client = create_client("https://api.tracetus.com")  # reads TRACETUS_API_KEY

issued = call(
    records_create.sync_detailed,
    client=client,
    body=IssueRecordRequest.from_dict({"schemaId": "tracetus:custody-event:1", "payload": {...}}),
    idempotency_key=new_idempotency_key(),
)

if issued.error is not None:
    # issued.error.code, .status, .request_id, .retry_after_s, .issues
    raise SystemExit(f"TraceTus refused: {issued.error.code}")

verified = call(verify_get.sync_detailed, client=client, id=issued.data.record.id)

# True, False, or None while the batch is open
verify_response_offline(verified.data)
```

Every response carries `env_label` (`simulation`, `testnet`, `mainnet`). Show it
next to anything that comes from the network.

## What it adds to the generated client

- **A retry never issues twice.** One `Idempotency-Key` per `POST`, kept across
  every attempt of that request, so a retry after a timeout is answered with the
  first answer instead of writing again. A `POST` answered `500` is not retried
  at all, because the write may have happened.
- **A failed call is a value.** `call()` answers `data`, `error` and `response`,
  and neither a refusal nor a dropped connection raises.
- **A timeout per attempt**, and `Retry-After` honoured up to a ceiling.
- **Offline verification** of an inclusion proof, with no call at all.

The full guide, in both languages, is at
[docs.tracetus.com/sdks](https://docs.tracetus.com/sdks/).

## How it is built

| Half | What it is |
|---|---|
| `src/tracetus_client/` | generated from `apps/api/openapi.json` by openapi-python-client. Never edited by hand. |
| `src/tracetus/` | everything else: the client factory, the retry transport, the typed error, the offline check. |

The behaviour lives in an `httpx` transport, **below** the generated client
(`src/tracetus/transport.py`), so every operation the generator produces — and
every operation it will produce — gets it with no line of its own.

```
sh scripts/generate.sh          # rewrites src/tracetus_client from the document
```

The pipeline diffs a fresh generation against what is committed, so a stale
copy fails the build.

## Develop

```
pip install -e ".[dev]"
pytest -q
ruff check src/tracetus tests examples && ruff format --check src/tracetus tests examples
sh scripts/generate.sh && git diff --exit-code -- src/tracetus_client
```

## Example

`examples/issue_and_verify.py` issues one custody event against a local
sandbox, polls `GET /v1/verify/{id}` until the worker seals the batch, and
checks the proof offline:

```
TRACETUS_API_URL=http://127.0.0.1:8787 TRACETUS_API_KEY=tk_... \
python examples/issue_and_verify.py
```

## Known limits

- **No pagination.** Three routes return a list — `GET /v1/connectors`,
  `GET /v1/connectors/{id}/devices` and `GET /v1/private-content` — and this
  client does not walk their pages for you yet: read a page, pass its
  `nextCursor` to the next call, stop when it is `null`.
- **No streaming.** Every answer is read in full before it is returned, which
  is what the routes publish today.
- **The API key is a bearer token.** Anything that can read the process's
  environment can read it.
- **Python 3.10 is the floor.** The generated client writes `X | None` unions at
  module level, which 3.9 cannot evaluate, so `pip` refuses this package there
  rather than letting it fail on import. 3.9 reached end of life in October
  2025.
