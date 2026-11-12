/**
 * How a client is configured, and what it refuses.
 *
 * Separated from the client itself so the defaults, the credential and the
 * injected clock live in one place rather than scattered through the request
 * path. Everything injectable is injectable for the same reason: a test of the
 * retry behaviour has to be exact and instant, not slow and approximate.
 *
 * A mistake here throws, with a literal `code`, before any request is sent.
 * The alternative — a base URL of `"not a url"` producing three connection
 * failures, or an `http://` address sending an issuer key in clear — is worse
 * than a loud failure at construction.
 */
import { TraceTusUsageError } from "./errors.js";
import { callGlobalFetch } from "./request.js";
import { DEFAULT_RETRY_LIMITS, type RetryLimits } from "./retry.js";

const API_KEY_VARIABLE = "TRACETUS_API_KEY";
/** Where `http://` is allowed: a machine talking to itself. */
const LOCAL_HOSTS = ["localhost", "127.0.0.1", "[::1]", "::1"];

/** One attempt's own patience. Generous: a batch of a thousand records is one call. */
export const DEFAULT_TIMEOUT_MS = 30_000;

export interface ClientOptions {
  /** Base URL of the API, without the version: the version is in the route. */
  baseUrl: string;
  /** Issuer key (`tk_...`). Read from `TRACETUS_API_KEY` when left out. */
  apiKey?: string | undefined;
  /** Milliseconds for one attempt. */
  timeoutMs?: number | undefined;
  /** Attempts in total, the first one included. One means no retry. */
  attempts?: number | undefined;
  /** Headers added to every call: a user agent, a trace header of your own. */
  headers?: Readonly<Record<string, string>> | undefined;
  /** A `fetch` of your own, for a runtime without a global one or for a test. */
  fetch?: typeof globalThis.fetch | undefined;
  /**
   * Waits, interruptibly. The signal is the call's: a wait between attempts
   * ends the moment the caller aborts.
   */
  sleep?: ((milliseconds: number, signal: AbortSignal | undefined) => Promise<void>) | undefined;
  /** Injected so the jitter is deterministic in a test. */
  random?: (() => number) | undefined;
  /** Injected so `Retry-After` as a date is deterministic in a test. */
  now?: (() => number) | undefined;
  /** Injected so the idempotency key is deterministic in a test. */
  newIdempotencyKey?: (() => string) | undefined;
  /**
   * Allows `http://` to a host that is not local. Off by default: an issuer key
   * on a plain connection is readable by anything on the path.
   */
  allowInsecureBaseUrl?: boolean | undefined;
}

export interface Settings {
  baseUrl: string;
  apiKey: string | undefined;
  timeoutMs: number;
  limits: RetryLimits;
  headers: Readonly<Record<string, string>>;
  fetch: typeof globalThis.fetch;
  /**
   * The wait between attempts. The signal is the caller's own, when they gave
   * one, and never the attempt's timeout: a timeout that already fired would
   * end the wait before it began.
   */
  sleep: (milliseconds: number, signal: AbortSignal | undefined) => Promise<void>;
  random: () => number;
  now: () => number;
  newIdempotencyKey: () => string;
}

/**
 * Reads `TRACETUS_API_KEY` where there is an environment to read, and says
 * nothing where there is not. No `process` import: this package runs in a
 * browser too.
 */
function keyFromEnvironment(): string | undefined {
  const runtime: unknown = globalThis;

  if (typeof runtime !== "object" || runtime === null || !("process" in runtime)) {
    return undefined;
  }

  const { process } = runtime;

  if (typeof process !== "object" || process === null || !("env" in process)) {
    return undefined;
  }

  const { env } = process;

  if (typeof env !== "object" || env === null || !(API_KEY_VARIABLE in env)) {
    return undefined;
  }

  const value = env[API_KEY_VARIABLE];

  return typeof value === "string" && value !== "" ? value : undefined;
}

/** Interruptible: a caller that aborts does not wait out a backoff first. */
function sleepFor(milliseconds: number, signal: AbortSignal | undefined): Promise<void> {
  return new Promise((done) => {
    if (signal === undefined) {
      setTimeout(done, milliseconds);

      return;
    }

    if (signal.aborted) {
      done();

      return;
    }

    const timer = setTimeout(() => {
      signal.removeEventListener("abort", onAbort);
      done();
    }, milliseconds);

    function onAbort(): void {
      clearTimeout(timer);
      done();
    }

    signal.addEventListener("abort", onAbort, { once: true });
  });
}

/**
 * The address has to be an address, and it has to be `https` unless it is this
 * machine. A key sent over `http://` to another host is a key anything on the
 * path can read.
 */
function checkBaseUrl(baseUrl: string, allowInsecure: boolean): string {
  if (baseUrl === "") {
    throw new TraceTusUsageError("BASE_URL_MISSING", "the client needs a baseUrl");
  }

  const parsed = URL.parse(baseUrl);

  if (parsed === null || (parsed.protocol !== "https:" && parsed.protocol !== "http:")) {
    throw new TraceTusUsageError(
      "BASE_URL_INVALID",
      `baseUrl is not an http or https address: ${baseUrl}`,
    );
  }

  if (parsed.protocol === "http:" && !allowInsecure && !LOCAL_HOSTS.includes(parsed.hostname)) {
    throw new TraceTusUsageError(
      "BASE_URL_INSECURE",
      `baseUrl is http to ${parsed.hostname}, which would send the API key in clear; use https, or set allowInsecureBaseUrl`,
    );
  }

  return baseUrl;
}

function checkTimeout(timeoutMs: number | undefined): number {
  if (timeoutMs === undefined) {
    return DEFAULT_TIMEOUT_MS;
  }

  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new TraceTusUsageError(
      "TIMEOUT_INVALID",
      "timeoutMs has to be a number of milliseconds above zero",
    );
  }

  return timeoutMs;
}

export function attemptsOf(attempts: number | undefined): { attempts?: number } {
  if (attempts === undefined) {
    return {};
  }

  if (!Number.isInteger(attempts) || attempts < 1) {
    throw new TraceTusUsageError(
      "ATTEMPTS_INVALID",
      "attempts has to be a whole number of at least 1",
    );
  }

  return { attempts };
}

/** An empty key is no key: it would send `Bearer` with nothing behind it. */
function given(value: string | undefined): string | undefined {
  return value === undefined || value === "" ? undefined : value;
}

export function settingsOf(options: ClientOptions): Settings {
  return {
    baseUrl: checkBaseUrl(options.baseUrl, options.allowInsecureBaseUrl === true),
    apiKey: given(options.apiKey) ?? keyFromEnvironment(),
    timeoutMs: checkTimeout(options.timeoutMs),
    limits: { ...DEFAULT_RETRY_LIMITS, ...attemptsOf(options.attempts) },
    headers: options.headers ?? {},
    fetch: options.fetch ?? callGlobalFetch,
    sleep: options.sleep ?? sleepFor,
    random: options.random ?? Math.random,
    now: options.now ?? Date.now,
    newIdempotencyKey: options.newIdempotencyKey ?? (() => crypto.randomUUID()),
  };
}
