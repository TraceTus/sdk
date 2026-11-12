/**
 * One HTTP attempt: build the address, send it, read the answer.
 *
 * Web APIs only — `fetch`, `AbortSignal`, `URL` — so this runs on Node, in a
 * browser, in a worker and on an edge runtime without a dependency and without
 * a shim. Two details of that are not cosmetic:
 *
 * - **The global `fetch` is called, never held.** A browser's `fetch` refuses
 *   to run detached from `window` ("Illegal invocation"), and edge runtimes
 *   enforce the same, so the default is a wrapper that calls the global at call
 *   time rather than a reference captured at construction.
 * - **A redirect is not followed.** Following one would carry the API key and
 *   the body to whatever host the redirect names, and would answer `data` for
 *   a request the API never saw.
 *
 * Nothing here decides whether to try again; that is `retry.ts`. Nothing here
 * knows an endpoint; the route comes from the generated manifest.
 */
import { TraceTusUsageError, type TransportErrorCode } from "./errors.js";

const JSON_MEDIA_TYPE = "application/json";
const RETRY_AFTER_HEADER = "retry-after";
const SUCCESS_FLOOR = 200;
const SUCCESS_CEILING = 300;
const REDIRECT_FLOOR = 300;
const REDIRECT_CEILING = 400;
/** What a browser reports for an opaque answer: no status of its own. */
const OPAQUE_STATUS = 0;
const MILLISECONDS_IN_SECOND = 1000;

/**
 * The global `fetch`, called rather than captured. `globalThis.fetch` detached
 * from its receiver throws in a browser; this is the whole fix.
 */
export const callGlobalFetch: typeof globalThis.fetch = (input, init) =>
  globalThis.fetch(input, init);

export interface Attempt {
  method: string;
  /** Path with its parameters already in place. */
  path: string;
  baseUrl: string;
  query: Readonly<Record<string, string>> | undefined;
  headers: Readonly<Record<string, string>>;
  /** Already serialised, so a body that cannot be serialised fails before any attempt. */
  body: string | undefined;
  signal: AbortSignal;
  /** True when the caller's own signal is what aborted, not the timeout. */
  aborted: () => boolean;
  fetch: typeof globalThis.fetch;
}

export type AttemptOutcome =
  | { kind: "answer"; response: Response; status: number; retryAfterSeconds: number | undefined }
  | { kind: "failure"; code: TransportErrorCode; message: string };

/** `/v1/records/{id}` with `{ id }` filled in, each value escaped. */
export function fillPath(path: string, parameters: Readonly<Record<string, unknown>>): string {
  return path.replace(/\{([^}]+)\}/g, (_whole, name: string) => {
    const value = parameters[name];

    if (value === undefined || value === null) {
      throw new TraceTusUsageError(
        "PATH_PARAMETER_MISSING",
        `the route ${path} needs the parameter ${name}`,
      );
    }

    return encodeURIComponent(String(value));
  });
}

export function buildUrl(attempt: Pick<Attempt, "baseUrl" | "path" | "query">): string {
  const base = attempt.baseUrl.endsWith("/") ? attempt.baseUrl : `${attempt.baseUrl}/`;
  const url = new URL(attempt.path.replace(/^\//, ""), base);

  for (const [name, value] of Object.entries(attempt.query ?? {})) {
    url.searchParams.set(name, value);
  }

  return url.toString();
}

export async function send(attempt: Attempt, now: () => number): Promise<AttemptOutcome> {
  const init: RequestInit = {
    method: attempt.method,
    headers: { accept: JSON_MEDIA_TYPE, ...attempt.headers },
    signal: attempt.signal,
    /** Never followed: a redirect would carry the key and the body elsewhere. */
    redirect: "manual",
  };

  if (attempt.body !== undefined) {
    init.body = attempt.body;
  }

  try {
    const response = await attempt.fetch(buildUrl(attempt), init);

    if (isRedirect(response.status) || isOpaqueRedirect(response)) {
      return {
        kind: "failure",
        code: "REDIRECTED",
        message: redirectMessage(response.status),
      };
    }

    return {
      kind: "answer",
      response,
      status: response.status,
      retryAfterSeconds: readRetryAfter(response.headers.get(RETRY_AFTER_HEADER), now),
    };
  } catch (error) {
    return failureOf(error, attempt.aborted());
  }
}

/**
 * A timeout, a dropped connection and the caller's own abort all arrive as a
 * rejection. The caller's signal is asked directly, because only the caller
 * knows that one was theirs.
 */
function failureOf(error: unknown, byCaller: boolean): AttemptOutcome {
  if (byCaller) {
    return { kind: "failure", code: "ABORTED", message: "the caller aborted the call" };
  }

  const timedOut = error instanceof Error && error.name === "TimeoutError";

  return {
    kind: "failure",
    code: timedOut ? "TIMEOUT" : "CONNECTION_FAILED",
    message: error instanceof Error ? error.name : "the request did not complete",
  };
}

export function isSuccess(status: number): boolean {
  return status >= SUCCESS_FLOOR && status < SUCCESS_CEILING;
}

function isRedirect(status: number): boolean {
  return status >= REDIRECT_FLOOR && status < REDIRECT_CEILING;
}

/**
 * The same redirect, as a browser hands it over.
 *
 * `redirect: "manual"` in a browser does not give the client the `30x`: it
 * gives an opaque response, status `0`, type `opaqueredirect`, no headers. Read
 * as a status it is not a redirect and not a success, so without this the one
 * thing that happened — the API answered "look elsewhere" — came back as
 * `BAD_ANSWER`, which says the opposite: that something unknown answered.
 */
function isOpaqueRedirect(response: Response): boolean {
  return response.type === "opaqueredirect" || response.status === OPAQUE_STATUS;
}

function redirectMessage(status: number): string {
  const what = status === OPAQUE_STATUS ? "a redirect" : `${status}`;

  return `the API answered ${what}; this client does not follow redirects, because following one would carry the API key and the body to another host`;
}

/** `Wed, 11 Nov 2026 12:00:05 GMT`, the one date form servers send. */
const HTTP_DATE = /^[A-Za-z]{3}, \d{2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} GMT$/;

/**
 * `Retry-After` in seconds, in both forms the HTTP specification allows: a
 * count of whole seconds, or a date.
 *
 * Both are matched exactly, and anything else is no wait at all rather than a
 * guess. `parseInt` would have taken `1.9` and `12abc` and been wrong twice,
 * and `Date.parse` alone takes `1.9` for a date in 2001 and would have waited
 * nothing at all on a header that meant two seconds. No wait is the safe
 * fallback: the backoff decides instead.
 */
export function readRetryAfter(header: string | null, now: () => number): number | undefined {
  if (header === null) {
    return undefined;
  }

  const trimmed = header.trim();

  if (/^\d+$/.test(trimmed)) {
    return Number(trimmed);
  }

  if (!HTTP_DATE.test(trimmed)) {
    return undefined;
  }

  const when = Date.parse(trimmed);

  if (Number.isNaN(when)) {
    return undefined;
  }

  return Math.max(0, Math.ceil((when - now()) / MILLISECONDS_IN_SECOND));
}
