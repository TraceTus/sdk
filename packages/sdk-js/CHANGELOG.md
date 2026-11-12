# @tracetus/sdk

Written by `changeset version` from the change descriptions of a release; the
entries below the next release line are added by it, not by hand.

## 0.1.0

The first version a customer can install.

- Methods named after the API's own operations (`tracetus.records.create`),
  derived from the OpenAPI document, with nothing hand-written per endpoint.
- A retry that never issues twice: one `Idempotency-Key` per call kept across
  every attempt, a `POST` answered `500` never retried, `Retry-After` honoured
  up to a ceiling in both the forms HTTP allows.
- A failed request as a value: exactly one of `data` and `error`, with the
  API's code, the HTTP status, the request id, `Retry-After`, and `uncertain`
  for the cases where the request may already have taken effect.
- Offline verification of an inclusion proof.
- Zero runtime dependencies, Web APIs only, ESM and CommonJS with their own
  declarations.

Renamed before the first publication, from a name that never reached npm.
