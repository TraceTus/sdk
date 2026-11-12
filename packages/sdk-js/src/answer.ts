/**
 * Reading an answer, and turning one into a typed error.
 *
 * Separated from sending because the two fail differently: sending fails when
 * nothing arrives, and this fails when something arrives that is not what the
 * route publishes. The second is the subtler one — an HTML error page from a
 * proxy, a `201` whose body is truncated — and the answer it deserves is not
 * "refused" but "the request may have taken effect".
 */
import { type ErrorIssue, type TraceTusError, isUncertain } from "./errors.js";
import type { AttemptOutcome } from "./request.js";

const JSON_MEDIA_TYPE = "application/json";
const TEXT_MEDIA_TYPE = "text/plain";
const REQUEST_ID_HEADER = "x-request-id";

function mediaTypeOf(response: Response): string {
  return response.headers.get("content-type")?.split(";")[0]?.trim() ?? "";
}

export type BodyOutcome = { kind: "read"; body: unknown } | { kind: "unreadable"; why: string };

/**
 * The body, as JSON when the route publishes JSON and as text when it publishes
 * text. A media type the route does not publish is unreadable rather than
 * guessed at: an HTML error page from a proxy is not an answer.
 */
export async function readBody(response: Response, expected: string): Promise<BodyOutcome> {
  const media = mediaTypeOf(response);

  if (expected === TEXT_MEDIA_TYPE) {
    return await readText(response);
  }

  if (media !== JSON_MEDIA_TYPE) {
    return { kind: "unreadable", why: `the answer is ${media === "" ? "untyped" : media}` };
  }

  try {
    return { kind: "read", body: await response.json() };
  } catch {
    return { kind: "unreadable", why: "the answer is not the JSON it declares" };
  }
}

async function readText(response: Response): Promise<BodyOutcome> {
  try {
    return { kind: "read", body: await response.text() };
  } catch {
    return { kind: "unreadable", why: "the answer could not be read" };
  }
}

interface ApiErrorBody {
  code: string;
  message: string;
  issues: ErrorIssue[];
}

function isIssue(value: unknown): value is ErrorIssue {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  return (
    "field" in value &&
    typeof value.field === "string" &&
    "code" in value &&
    typeof value.code === "string" &&
    "detail" in value &&
    typeof value.detail === "string"
  );
}

/** Reads the API's own error body. An answer outside the contract gives nothing. */
export function readApiError(body: unknown): ApiErrorBody | undefined {
  if (typeof body !== "object" || body === null || !("error" in body)) {
    return undefined;
  }

  const { error } = body;

  if (typeof error !== "object" || error === null) {
    return undefined;
  }

  const code = "code" in error ? error.code : undefined;
  const message = "message" in error ? error.message : undefined;

  if (typeof code !== "string" || typeof message !== "string") {
    return undefined;
  }

  const issues = "issues" in error && Array.isArray(error.issues) ? error.issues : [];

  return { code, message, issues: issues.filter(isIssue) };
}

export interface ErrorContext {
  response: Response;
  status: number;
  retryAfterSeconds: number | undefined;
  attempts: number;
  /** The request's method: what a failed answer means depends on it. */
  method: string;
}

const SERVER_ERROR_FLOOR = 500;
const SAFE_METHODS = ["GET", "HEAD", "OPTIONS"];

function isSafe(method: string): boolean {
  return SAFE_METHODS.includes(method.toUpperCase());
}

/**
 * Whether the request may already have taken effect, from the answer alone.
 *
 * A read that failed changed nothing, whatever it answered. A write is the
 * question, and the honest answer is "it depends on what answered":
 *
 * - **A refusal the API published** (`422`, `409 DUPLICATE_RECORD`, ...) is a
 *   decision about the request. It wrote nothing, and says so.
 * - **A `5xx`** is the server saying it failed, not that it did nothing. A
 *   `500` can come from a commit that landed and an answer that did not, and a
 *   `502` or `504` from a gateway that never saw the answer to a request the
 *   API served in full.
 * - **Anything outside the contract** — an HTML error page, a body that is not
 *   the published shape — did not come from a part of the stack that knows
 *   whether the write happened.
 *
 * Reporting those last two as certain is the dangerous direction: a caller that
 * trusts it issues again under a *new* key and writes twice.
 */
function isUncertainAnswer(context: ErrorContext, inContract: boolean): boolean {
  if (isSafe(context.method)) {
    return false;
  }

  return context.status >= SERVER_ERROR_FLOOR || !inContract;
}

function requestIdOf(response: Response): string | undefined {
  return response.headers.get(REQUEST_ID_HEADER) ?? undefined;
}

export function errorFromAnswer(body: unknown, context: ErrorContext): TraceTusError {
  const found = readApiError(body);
  const uncertain = isUncertainAnswer(context, found !== undefined);
  const shared = {
    status: context.status,
    requestId: requestIdOf(context.response),
    retryAfterSeconds: context.retryAfterSeconds,
    attempts: context.attempts,
    uncertain,
  };
  const warning = uncertain ? "; the request may have taken effect" : "";

  if (found === undefined) {
    return {
      ...shared,
      code: "BAD_ANSWER",
      message: `the API answered ${context.status} outside the published contract${warning}`,
      issues: [],
    };
  }

  return {
    ...shared,
    code: found.code,
    message: `${found.message}${warning}`,
    issues: found.issues,
  };
}

/**
 * The API accepted the request and the answer could not be read. The write
 * happened; what is missing is only the account of it.
 */
export function errorFromUnreadable(why: string, context: ErrorContext): TraceTusError {
  return {
    code: "ANSWER_UNREADABLE",
    message: `${why}; the request may have taken effect`,
    status: context.status,
    requestId: requestIdOf(context.response),
    retryAfterSeconds: context.retryAfterSeconds,
    issues: [],
    attempts: context.attempts,
    uncertain: true,
  };
}

export function errorFromFailure(
  failure: Extract<AttemptOutcome, { kind: "failure" }>,
  attempts: number,
): TraceTusError {
  return {
    code: failure.code,
    message: failure.message,
    status: 0,
    requestId: undefined,
    retryAfterSeconds: undefined,
    issues: [],
    attempts,
    uncertain: isUncertain(failure.code),
  };
}

/** The attempts ran out while an earlier attempt of this call was still being served. */
export function errorFromInProgress(context: ErrorContext): TraceTusError {
  return {
    code: "OUTCOME_UNKNOWN",
    message:
      "an earlier attempt of this call is still being served; retry with the same Idempotency-Key to read its answer",
    status: context.status,
    requestId: requestIdOf(context.response),
    retryAfterSeconds: context.retryAfterSeconds,
    issues: [],
    attempts: context.attempts,
    uncertain: true,
  };
}
