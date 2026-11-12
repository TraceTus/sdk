/**
 * What a failed call gives back.
 *
 * A failed request is a value here, not an exception: every call answers
 * exactly one of `data` and `error`, and nothing throws because the API refused
 * or because the network did. A thrown error from this package means the
 * calling code is wrong (`TraceTusUsageError`) or this package has a bug.
 *
 * The code is what a client should branch on. When the API answered, it is the
 * API's own code (`PAYLOAD_INVALID`, `RATE_LIMITED`, ...); when no usable
 * answer arrived, it is one of this package's, and those are a closed list so a
 * `switch` over them is complete.
 */

/**
 * Codes this package produces itself. Each one is a different thing for the
 * caller to do, which is why they are not one code with a message.
 *
 * - `TIMEOUT`: the attempt passed the timeout. Nothing is known about the
 *   request's effect; retrying with the same key is safe.
 * - `CONNECTION_FAILED`: the connection did not open, or dropped. Same.
 * - `ABORTED`: the caller's own signal fired. The call stopped at once and was
 *   not retried.
 * - `REDIRECTED`: the API answered a redirect, which this client does not
 *   follow — following one would carry the key and the body to another host.
 * - `ANSWER_UNREADABLE`: the API accepted the request and the answer could not
 *   be read. **The request may have taken effect**; read the resource, or retry
 *   with the same key to get the stored answer.
 * - `BAD_ANSWER`: something answered outside the published contract.
 * - `OUTCOME_UNKNOWN`: the attempts ran out while an earlier attempt of this
 *   same call was still being served. Retry with the **same** key: the answer
 *   will be the first attempt's.
 */
export const TRANSPORT_ERROR_CODES = [
  "TIMEOUT",
  "CONNECTION_FAILED",
  "ABORTED",
  "REDIRECTED",
  "ANSWER_UNREADABLE",
  "BAD_ANSWER",
  "OUTCOME_UNKNOWN",
] as const;

export type TransportErrorCode = (typeof TRANSPORT_ERROR_CODES)[number];

export function isTransportErrorCode(code: string): code is TransportErrorCode {
  return TRANSPORT_ERROR_CODES.some((candidate) => candidate === code);
}

/**
 * Codes after which the request may already have taken effect. A client that
 * must not act twice reads the resource, or retries with the same key.
 */
const UNCERTAIN_CODES: readonly TransportErrorCode[] = [
  "TIMEOUT",
  "CONNECTION_FAILED",
  "ANSWER_UNREADABLE",
  "OUTCOME_UNKNOWN",
];

export function isUncertain(code: string): boolean {
  return UNCERTAIN_CODES.some((candidate) => candidate === code);
}

export interface ErrorIssue {
  field: string;
  code: string;
  detail: string;
}

export interface TraceTusError {
  /** The API's code when it answered; one of `TRANSPORT_ERROR_CODES` when it did not. */
  code: string;
  message: string;
  /** HTTP status of the answer. Zero when no answer arrived. */
  status: number;
  /** `x-request-id` of the answer: the one thing worth quoting in a support thread. */
  requestId: string | undefined;
  /** Seconds the API asked the client to wait, when it asked. */
  retryAfterSeconds: number | undefined;
  /** What the API found wrong, field by field. Never the value it received. */
  issues: readonly ErrorIssue[];
  /** Attempts made, the first one included. */
  attempts: number;
  /**
   * True when the request may already have taken effect. Never true for a
   * refusal the API answered: those did nothing.
   */
  uncertain: boolean;
}

/** Codes for a mistake in the calling code, which throws rather than answering. */
export const USAGE_ERROR_CODES = [
  "BASE_URL_MISSING",
  "BASE_URL_INVALID",
  "BASE_URL_INSECURE",
  "TIMEOUT_INVALID",
  "ATTEMPTS_INVALID",
  "PATH_PARAMETER_MISSING",
  "BODY_NOT_SERIALISABLE",
  "CLIENT_SHAPE_INVALID",
] as const;

export type UsageErrorCode = (typeof USAGE_ERROR_CODES)[number];

/**
 * A mistake in the calling code, not a refusal by the API. It throws, unlike
 * every refusal, because there is no answer to hand back and no retry that
 * would help. It carries a literal `code` so a caller can tell them apart
 * without reading the message.
 */
export class TraceTusUsageError extends Error {
  readonly code: UsageErrorCode;

  constructor(code: UsageErrorCode, message: string) {
    super(message);
    this.name = "TraceTusUsageError";
    this.code = code;
  }
}
