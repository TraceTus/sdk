/**
 * TraceTus client for JavaScript and TypeScript.
 *
 * Two halves, and the seam between them is the point. The generated half is
 * the types and the route table, both written by
 * `pnpm --filter @tracetus/sdk generate` out of `apps/api/openapi.json` and
 * never by hand, as the repository's rules require. The half above it is small
 * and has nothing per endpoint: the methods are the API's own operation names,
 * so a route the API adds shows up here on the next generation.
 *
 * What it adds to a bare `fetch`:
 *
 * - **A retry never issues twice.** One `Idempotency-Key` per `POST`, kept
 *   across every attempt of that call, so a timeout that is retried is
 *   answered with the first answer. A `POST` answered `500` is not retried at
 *   all.
 * - **A failed request is a value.** Every call answers
 *   `{ data, error, response }` and throws for neither a refusal nor a dropped
 *   connection. The typed error carries the API's `code`, the HTTP status, the
 *   request id and `Retry-After`.
 * - **A timeout per attempt**, and `Retry-After` honoured up to a ceiling.
 * - **Offline verification** of an inclusion proof, with no call at all.
 *
 * Web APIs only — `fetch`, `AbortSignal`, `crypto.randomUUID`, `URL` — and no
 * dependencies, so it runs on Node, in a browser, in a worker and on an edge
 * runtime.
 */
export { createTraceTusClient } from "./client.js";
export { DEFAULT_TIMEOUT_MS, type ClientOptions } from "./settings.js";
export {
  DEFAULT_ATTEMPTS,
  DEFAULT_BACKOFF_MS,
  DEFAULT_MAX_BACKOFF_MS,
  DEFAULT_MAX_RETRY_AFTER_SECONDS,
  IN_PROGRESS_CODE,
} from "./retry.js";
export {
  TRANSPORT_ERROR_CODES,
  TraceTusUsageError,
  USAGE_ERROR_CODES,
  isTransportErrorCode,
  isUncertain,
  type ErrorIssue,
  type TraceTusError,
  type TransportErrorCode,
  type UsageErrorCode,
} from "./errors.js";
export {
  verifyProofOffline,
  verifyResponseOffline,
  type VerifiableResponse,
} from "./offline.js";
export type {
  ActionOf,
  Call,
  CallOptions,
  DataOf,
  OperationId,
  RequestInput,
  ResourceOf,
  Result,
  TraceTusClient,
} from "./types.js";
export { OPERATIONS, type OperationRoute } from "./generated/operations.js";
export type { components, operations, paths } from "./generated/openapi.js";

import type { components } from "./generated/openapi.js";

/** The shapes a customer's code names most often, under shorter names. */
export type IssueRecordRequest = components["schemas"]["IssueRecordRequest"];
export type IssueBatchRequest = components["schemas"]["IssueBatchRequest"];
export type IssuedRecord = components["schemas"]["IssueRecordResponse"];
export type IssuedBatch = components["schemas"]["IssueBatchResponse"];
export type RecordDetail = components["schemas"]["RecordDetail"];
export type VerifyResponse = components["schemas"]["VerifyResponse"];
export type StorePrivateContentRequest = components["schemas"]["StorePrivateContentRequest"];
export type PrivateContent = components["schemas"]["PrivateContent"];
export type PrivateContentWithContent = components["schemas"]["PrivateContentWithContent"];
export type PrivateContentPage = components["schemas"]["PrivateContentPage"];
export type ApiErrorBody = components["schemas"]["ErrorResponse"];
export type CreateConnectorRequest = components["schemas"]["CreateConnectorRequest"];
export type CreatedConnector = components["schemas"]["CreateConnectorResponse"];
export type ConnectorList = components["schemas"]["ConnectorListResponse"];
export type AddConnectorDeviceRequest = components["schemas"]["AddConnectorDeviceRequest"];
export type ConnectorDeviceList = components["schemas"]["ConnectorDeviceListResponse"];
