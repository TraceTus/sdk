import {
  errorFromAnswer,
  errorFromFailure,
  errorFromInProgress,
  errorFromUnreadable,
  readApiError,
  readBody,
} from "./answer.js";
/**
 * The client, built from the operation names.
 *
 * There is no code per endpoint here, and that is the design: the generated
 * manifest says which method and path each `operationId` means, and the loop
 * at the bottom turns `records.create` into `tracetus.records.create`. A route
 * added to the API appears here after `pnpm --filter @tracetus/sdk generate`,
 * with its own types, and this file does not change.
 *
 * What this layer adds to a bare `fetch`:
 *
 * - an `Idempotency-Key` per `POST`, kept across every attempt of that call,
 *   so a retry after a timeout is answered rather than written again;
 * - a timeout per attempt, and retries that honour `Retry-After`;
 * - exactly one of `data` and `error` on every answer, and never a throw for a
 *   request that failed;
 * - the environment label and everything else exactly as the API sent it.
 */
import { type TraceTusError, TraceTusUsageError } from "./errors.js";
import { OPERATIONS, type OperationRoute } from "./generated/operations.js";
import { type RawInput, expectedMediaOf, headersFor, isRawInput, serialise } from "./input.js";
import { type Attempt, type AttemptOutcome, fillPath, isSuccess, send } from "./request.js";
import { IN_PROGRESS_CODE, decideRetry } from "./retry.js";
import { type ClientOptions, type Settings, attemptsOf, settingsOf } from "./settings.js";
import type { CallOptions, Result, TraceTusClient } from "./types.js";

const NAME_SEPARATOR = ".";
/** Failures that are the answer, not a reason to send again. */
const STOPS_THE_CALL: readonly string[] = ["ABORTED", "REDIRECTED"];
const CONFLICT = 409;

interface Call {
  settings: Settings;
  route: OperationRoute;
  input: RawInput;
  options: CallOptions;
}

function failed(error: TraceTusError, response: Response | undefined): Result<never> {
  return { data: undefined, error, response };
}

/** The answer, read as the route publishes it; anything else is a typed error. */
async function finish(
  outcome: Extract<AttemptOutcome, { kind: "answer" }>,
  call: Call,
  attempts: number,
): Promise<Result<unknown>> {
  const context = { ...outcome, attempts, method: call.route.method };
  const read = await readBody(outcome.response, expectedMediaOf(call.route));

  if (!isSuccess(outcome.status)) {
    const body = read.kind === "read" ? read.body : undefined;

    if (isStillRunning(outcome.status, body)) {
      return failed(errorFromInProgress(context), outcome.response);
    }

    return failed(errorFromAnswer(body, context), outcome.response);
  }

  if (read.kind === "unreadable") {
    return failed(errorFromUnreadable(read.why, context), outcome.response);
  }

  return { data: read.body, error: undefined, response: outcome.response };
}

function isStillRunning(status: number, body: unknown): boolean {
  return status === CONFLICT && readApiError(body)?.code === IN_PROGRESS_CODE;
}

/**
 * Sends, and sends again while the policy says the answer may change. The
 * headers and the body are built once, before the first attempt, which is what
 * keeps one `Idempotency-Key` and one set of bytes across all of them.
 */
async function perform(call: Call): Promise<Result<unknown>> {
  const { settings } = call;
  const limits = { ...settings.limits, ...attemptsOf(call.options.attempts) };
  const body = serialise(call.input.body);
  const attempt: Omit<Attempt, "signal" | "aborted"> = {
    method: call.route.method,
    path: fillPath(call.route.path, call.input.path ?? {}),
    baseUrl: settings.baseUrl,
    query: call.input.query,
    headers: headersFor(settings, call.route, call.input, body),
    body,
    fetch: settings.fetch,
  };
  const caller = call.options.signal;

  for (let made = 1; ; made += 1) {
    /** A fresh timeout per attempt; the caller's signal spans all of them. */
    const timeout = AbortSignal.timeout(call.options.timeoutMs ?? settings.timeoutMs);
    const signal = caller === undefined ? timeout : AbortSignal.any([timeout, caller]);
    const outcome = await send(
      { ...attempt, signal, aborted: () => caller?.aborted === true },
      settings.now,
    );

    const answered = outcome.kind === "answer" ? outcome : undefined;

    /**
     * Two failures are answers in themselves rather than something to try
     * again: the caller's own abort, which is the one failure they asked for,
     * and a redirect, which this client does not follow. Retrying a redirect
     * would treat "the API is somewhere else" as "nothing answered" and spend
     * every attempt on it.
     */
    if (outcome.kind === "failure" && STOPS_THE_CALL.includes(outcome.code)) {
      return failed(errorFromFailure(outcome, made), undefined);
    }
    const decision = decideRetry({
      method: call.route.method,
      status: answered?.status,
      code: await codeOf(answered),
      retryAfterSeconds: answered?.retryAfterSeconds,
      attempt: made,
      limits,
      random: settings.random,
    });

    if (!decision.retry) {
      if (answered !== undefined) {
        return await finish(answered, call, made);
      }

      return failed(errorFromFailure(asFailure(outcome), made), undefined);
    }

    /**
     * Only the caller's signal reaches the wait. Passing the attempt's timeout
     * would hand the backoff a signal that has *already* fired whenever the
     * attempt timed out, so every retry after a timeout left immediately and
     * the backoff did not exist.
     */
    await settings.sleep(decision.waitMs, caller);

    if (caller?.aborted === true) {
      return failed(
        errorFromFailure(
          { kind: "failure", code: "ABORTED", message: "the caller aborted the call" },
          made,
        ),
        undefined,
      );
    }
  }
}

/**
 * The API's code, read from a clone so the answer itself is still unread. Only
 * a `409` can change the policy's mind, so nothing else is cloned.
 */
async function codeOf(
  answered: Extract<AttemptOutcome, { kind: "answer" }> | undefined,
): Promise<string | undefined> {
  if (answered === undefined || answered.status !== CONFLICT) {
    return undefined;
  }

  const body = await answered.response
    .clone()
    .json()
    .catch(() => undefined);

  return readApiError(body)?.code;
}

/** Inside the loop the answer branch has already returned, so this is the rest. */
function asFailure(outcome: AttemptOutcome): Extract<AttemptOutcome, { kind: "failure" }> {
  if (outcome.kind === "answer") {
    throw new TraceTusUsageError("CLIENT_SHAPE_INVALID", "an answer reached the failure path");
  }

  return outcome;
}

function callFor(settings: Settings, route: OperationRoute) {
  return async (input?: unknown, options?: CallOptions): Promise<Result<unknown>> => {
    return await perform({
      settings,
      route,
      input: isRawInput(input) ? input : {},
      options: options ?? {},
    });
  };
}

/**
 * Builds `{ records: { create, createBatch, get }, verify: { get }, ... }` out
 * of the operation names. The type says the same thing, derived from the same
 * document, so the two cannot drift.
 */
function buildNamespaces(settings: Settings): Record<string, Record<string, unknown>> {
  const client: Record<string, Record<string, unknown>> = {};

  for (const [id, route] of Object.entries(OPERATIONS)) {
    const separator = id.indexOf(NAME_SEPARATOR);
    const resource = id.slice(0, separator);
    const action = id.slice(separator + NAME_SEPARATOR.length);

    client[resource] ??= {};
    client[resource][action] = callFor(settings, route);
  }

  return client;
}

export function createTraceTusClient(options: ClientOptions): TraceTusClient {
  const built = buildNamespaces(settingsOf(options));

  if (!isClient(built)) {
    throw new TraceTusUsageError(
      "CLIENT_SHAPE_INVALID",
      "the generated operations do not cover the client's shape",
    );
  }

  return built;
}

/**
 * Every operation name has a function at its place. The built object and the
 * type both come from the same document, so this only fails if the generated
 * manifest and the generated types went out of step, which
 * `test/generated.test.ts` is there to prevent.
 */
function isClient(value: Record<string, Record<string, unknown>>): value is TraceTusClient {
  return Object.keys(OPERATIONS).every((id) => {
    const separator = id.indexOf(NAME_SEPARATOR);
    const resource = value[id.slice(0, separator)];

    return typeof resource?.[id.slice(separator + NAME_SEPARATOR.length)] === "function";
  });
}
