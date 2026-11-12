# @tracetus/sdk

TraceTus client for JavaScript and TypeScript: issue records, read proofs, and
check an inclusion proof without asking anybody.

```bash
npm install @tracetus/sdk
```

Zero dependencies. Web APIs only — `fetch`, `AbortSignal`, `crypto.randomUUID`,
`URL` — so it runs on **Node 20.3 and up** (where `AbortSignal.any` arrived), in
a browser, in a worker and on an edge runtime. ESM and CommonJS, each with its
own declarations.

## Use

```ts
import { createTraceTusClient, verifyResponseOffline } from "@tracetus/sdk";

const tracetus = createTraceTusClient({
  baseUrl: "https://api.tracetus.com",
  apiKey: process.env.TRACETUS_API_KEY,
});

const issued = await tracetus.records.create({
  body: { schemaId: "tracetus:custody-event:1", payload: { /* as the schema says */ } },
});

if (issued.error !== undefined) {
  // issued.error.code: PAYLOAD_INVALID, PAYLOAD_PERSONAL_DATA, SCHEMA_UNKNOWN, ...
  throw new Error(`TraceTus refused: ${issued.error.code}`);
}

const verified = await tracetus.verify.get({ path: { id: issued.data.record.id } });

if (verified.error !== undefined) {
  throw new Error(`TraceTus refused: ${verified.error.code}`);
}

// true, false, or null while the batch is not sealed yet
verifyResponseOffline(verified.data);
```

Every response carries `envLabel` (`simulation`, `testnet`, `mainnet`). Show it
next to anything that comes from the network.

## What it adds to a bare `fetch`

- **A retry never issues twice.** One `Idempotency-Key` per `POST`, kept across
  every attempt of that call, so a retry after a timeout is answered with the
  first answer instead of writing again. A `POST` answered `500` is not retried
  at all, because the write may have happened.
- **A failed request is a value.** Every call answers
  `{ data, error, response }`, with exactly one of `data` and `error` set, so
  checking `error` narrows `data` for the compiler. Nothing throws for a refusal
  or a dropped connection. The typed error carries the API's `code`, the HTTP
  status, the request id, `Retry-After`, and `uncertain` — true when the request
  may already have taken effect.
- **A timeout per attempt**, and `Retry-After` honoured up to a ceiling, past
  which the call comes back and lets you decide.
- **Offline verification** of an inclusion proof, with no call at all.

The full guide, in both languages, is at
[docs.tracetus.com/sdks](https://docs.tracetus.com/sdks/).

## How it is built

Two halves, and the seam between them is the point.

| Half | What it is |
|---|---|
| `src/generated/openapi.ts` | the types, from `apps/api/openapi.json` through openapi-typescript. Its `operations` interface is keyed by `operationId`. |
| `src/generated/operations.ts` | the same names at runtime: which method and path each `operationId` means. |
| `src/` | everything else: the client, the retry policy, one HTTP attempt, the typed error, the offline check. |

**Nothing above the generated half knows an endpoint.** The methods are built
from the operation names, and the types are derived from the same names, so a
route the API adds appears as `tracetus.<resource>.<action>` after one command
and no hand-written line:

```
pnpm --filter @tracetus/sdk generate
```

`test/generated.test.ts` refuses a stale copy of either generated file, and
refuses the two disagreeing with each other.

## Develop

```
pnpm --filter @tracetus/sdk generate     # both generated files, from the document
pnpm --filter @tracetus/sdk build        # ESM, CommonJS and declarations, through tsup
pnpm --filter @tracetus/sdk test         # the client, the retry policy, the types
pnpm --filter @tracetus/sdk smoke        # npm pack, install into an empty project, run it
```

One of the suites runs in a real Chromium, which is how a client that calls a
detached global `fetch` gets caught: Node allows it, a browser and an edge
runtime do not. Install the browser once with `pnpm --filter @tracetus/sdk exec
playwright install chromium-headless-shell`.

The client is also exercised against a running API, in the suites of the
platform that serves it. Those live where the API does.

`@tracetus/core` is bundled into the build rather than depended on: it is our
own pure domain code — the Merkle rule that builds a proof is the one that
checks it — and bundling is what keeps the published package at zero runtime
dependencies.

The smoke test is the only check that exercises what npm would publish: the
`files` list, the `exports` map, the declarations and both module formats. A
build that works from source and breaks once installed fails there and nowhere
else.

## Private content

Whatever could identify a person — a coordinate, the track of a vehicle, the
exact place of an installation — does not belong in a record. Store it first
and cite the identifier you get back:

```ts
const kept = await tracetus.privateContent.create({
  body: { content: { latitude: -16.6799, longitude: -49.255 }, purpose: "device-location" },
});

if (kept.error !== undefined) {
  throw new Error(`TraceTus refused: ${kept.error.code}`);
}

await tracetus.records.create({
  body: {
    // a schema whose field is marked `x-private-ref`
    schemaId: "tracetus:device:1",
    payload: { installationPlaceRef: kept.data.content.id },
  },
});
```

The content comes back only to the issuer that stored it
(`GET /private-content/{id}`), is erasable (`DELETE /private-content/{id}`,
and `410` from then on) and never reaches a record, a webhook, the public
verifier or the network. A field may only carry such an identifier when its
schema marks it `x-private-ref`.

## Example

`examples/issue-and-verify.ts` issues one custody event against a local
sandbox, polls `GET /v1/verify/{id}` until the worker seals the batch, and
checks the proof offline:

```
TRACETUS_API_URL=http://127.0.0.1:8787 TRACETUS_API_KEY=tk_... \
pnpm --filter @tracetus/sdk example
```

## Known limits

- **No pagination.** Three routes return a list — `GET /v1/connectors`,
  `GET /v1/connectors/{id}/devices` and `GET /v1/private-content` — and this
  client does not walk their pages for you yet: read a page, pass its
  `nextCursor` to the next call, stop when it is `null`.
- **The API key is a bearer token.** Anything that can read your process's
  environment can read it. In a browser, never ship an issuer key: issue from
  your own server.
- **`GET /v1/verify/*` needs no key**, so a client built without one still
  verifies. Every other route answers `401`.
