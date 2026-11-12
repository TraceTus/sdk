/**
 * When to try again, and how long to wait first.
 *
 * The rule that matters: **a retry must never issue twice.** Every `POST`
 * carries one `Idempotency-Key` for all of its attempts, so a retry after a
 * timeout is answered with the first answer instead of writing again. What that
 * does not cover is an answer that says the server failed in an unknown way: a
 * `500` on a `POST` may or may not have written, and the API deliberately
 * refuses to replay such a key, so trying again would only produce a `409`.
 * It is not retried.
 *
 * - **No answer at all** (connection refused, timeout): try again, with
 *   exponential backoff and full jitter.
 * - **`429` and `503`**: nothing ran, so try again, waiting what `Retry-After`
 *   says — up to a ceiling, past which the client stops and hands the wait back
 *   to the caller, who knows better than this library whether to sit on it.
 * - **`409 IDEMPOTENCY_KEY_IN_PROGRESS`**: an earlier attempt of this same call
 *   is still being served. Waiting and asking again is the only way to learn
 *   its answer, so it is retried like a `503`; when the attempts run out the
 *   caller is told the outcome is unknown and that the same key must be reused.
 * - **Another `5xx`**: try again only on a method that changes nothing. On a
 *   `POST`, stop.
 * - **Any `4xx` other than those**: the request is wrong; trying again would
 *   produce the same refusal.
 * - **The caller's abort**: stop at once. It is the one failure the caller
 *   asked for.
 *
 * The clock, the sleep and the random source all come in as parameters, so the
 * tests of this policy are deterministic and instant.
 */

const MILLISECONDS_IN_SECOND = 1000;
const TOO_MANY_REQUESTS = 429;
const SERVICE_UNAVAILABLE = 503;
const CONFLICT = 409;
const SERVER_ERROR_FLOOR = 500;
const BACKOFF_BASE = 2;

/** The API's code for "an earlier attempt of this call has not answered yet". */
export const IN_PROGRESS_CODE = "IDEMPOTENCY_KEY_IN_PROGRESS";

/** First wait of the backoff; each attempt doubles it. */
export const DEFAULT_BACKOFF_MS = 250;
/** Ceiling of one backoff wait, jitter applied inside it. */
export const DEFAULT_MAX_BACKOFF_MS = 8_000;
/** Longest `Retry-After` the client will sit through on its own. */
export const DEFAULT_MAX_RETRY_AFTER_SECONDS = 60;
/** Attempts in total, the first one included. */
export const DEFAULT_ATTEMPTS = 3;

export interface RetryLimits {
  attempts: number;
  backoffMs: number;
  maxBackoffMs: number;
  maxRetryAfterSeconds: number;
}

export const DEFAULT_RETRY_LIMITS: RetryLimits = {
  attempts: DEFAULT_ATTEMPTS,
  backoffMs: DEFAULT_BACKOFF_MS,
  maxBackoffMs: DEFAULT_MAX_BACKOFF_MS,
  maxRetryAfterSeconds: DEFAULT_MAX_RETRY_AFTER_SECONDS,
};

export interface RetryQuestion {
  /** HTTP method of the request, so a write is not retried on an unknown failure. */
  method: string;
  /** Status of the answer, or `undefined` when none arrived. */
  status: number | undefined;
  /** The API's own code, when it answered one. */
  code: string | undefined;
  /** `Retry-After` of the answer, in seconds, when it carried one. */
  retryAfterSeconds: number | undefined;
  /** Attempts already made, this one included. */
  attempt: number;
  limits: RetryLimits;
  /** A number in `[0, 1)`; injected so a test is deterministic. */
  random: () => number;
}

export type RetryDecision = { retry: false } | { retry: true; waitMs: number };

const SAFE_METHODS = ["GET", "HEAD", "OPTIONS"];

function isSafe(method: string): boolean {
  return SAFE_METHODS.includes(method.toUpperCase());
}

/** Exponential, with full jitter, under the ceiling. */
function backoffFor(question: RetryQuestion): number {
  const { limits } = question;
  const grown = limits.backoffMs * BACKOFF_BASE ** (question.attempt - 1);

  return Math.round(Math.min(grown, limits.maxBackoffMs) * question.random());
}

function waitOrStop(question: RetryQuestion): RetryDecision {
  const { retryAfterSeconds, limits } = question;

  if (retryAfterSeconds === undefined) {
    return { retry: true, waitMs: backoffFor(question) };
  }

  if (retryAfterSeconds > limits.maxRetryAfterSeconds) {
    return { retry: false };
  }

  return { retry: true, waitMs: retryAfterSeconds * MILLISECONDS_IN_SECOND };
}

/** An earlier attempt of this very call is still being served. */
function isInProgress(question: RetryQuestion): boolean {
  return question.status === CONFLICT && question.code === IN_PROGRESS_CODE;
}

export function decideRetry(question: RetryQuestion): RetryDecision {
  if (question.attempt >= question.limits.attempts) {
    return { retry: false };
  }

  const { status } = question;

  if (status === undefined) {
    return { retry: true, waitMs: backoffFor(question) };
  }

  if (status === TOO_MANY_REQUESTS || status === SERVICE_UNAVAILABLE || isInProgress(question)) {
    return waitOrStop(question);
  }

  if (status >= SERVER_ERROR_FLOOR && isSafe(question.method)) {
    return { retry: true, waitMs: backoffFor(question) };
  }

  return { retry: false };
}
