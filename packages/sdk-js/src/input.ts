/**
 * Turning what the caller passed into the parts of one request.
 *
 * Separated from the client because it answers a different question: the client
 * decides how many attempts a call gets and what to do with each answer, and
 * this decides what every one of those attempts sends. Both of its rules are
 * about not sending something twice — one header name in two casings, or one
 * body under two idempotency keys — so they are read together or not at all.
 */
import { TraceTusUsageError } from "./errors.js";
import type { OperationRoute } from "./generated/operations.js";
import type { Settings } from "./settings.js";

const IDEMPOTENCY_HEADER = "Idempotency-Key";
const AUTHORIZATION_HEADER = "authorization";
const CONTENT_TYPE_HEADER = "content-type";
const JSON_MEDIA_TYPE = "application/json";
export interface RawInput {
  body?: unknown;
  path?: Readonly<Record<string, unknown>>;
  query?: Readonly<Record<string, string>>;
  headers?: Readonly<Record<string, string>>;
}

/**
 * Headers merged so that one name cannot arrive twice in two casings. HTTP
 * header names are case-insensitive, and a caller writing `idempotency-key`
 * where this client writes `Idempotency-Key` must replace it, not add to it.
 */
function mergeHeaders(
  ...layers: readonly Readonly<Record<string, string>>[]
): Record<string, string> {
  const merged = new Map<string, [string, string]>();

  for (const layer of layers) {
    for (const [name, value] of Object.entries(layer)) {
      merged.set(name.toLowerCase(), [name, value]);
    }
  }

  return Object.fromEntries([...merged.values()]);
}

export function headersFor(
  settings: Settings,
  route: OperationRoute,
  input: RawInput,
  body: string | undefined,
): Record<string, string> {
  const own: Record<string, string> = {};

  if (settings.apiKey !== undefined) {
    own[AUTHORIZATION_HEADER] = `Bearer ${settings.apiKey}`;
  }

  if (body !== undefined) {
    own[CONTENT_TYPE_HEADER] = JSON_MEDIA_TYPE;
  }

  /**
   * One key for every attempt of this call. A caller with a key of its own —
   * derived from the event it is recording, say — keeps it, in any casing.
   */
  if (route.method === "POST") {
    own[IDEMPOTENCY_HEADER] = settings.newIdempotencyKey();
  }

  return mergeHeaders(settings.headers, own, input.headers ?? {});
}

/** Serialised once, before the first attempt: a body that cannot be sent fails loudly. */
export function serialise(body: unknown): string | undefined {
  if (body === undefined) {
    return undefined;
  }

  try {
    return JSON.stringify(body);
  } catch (error) {
    throw new TraceTusUsageError(
      "BODY_NOT_SERIALISABLE",
      `the body cannot be serialised as JSON: ${error instanceof Error ? error.message : "unknown"}`,
    );
  }
}

/**
 * What this route answers on success, so a wrong media type is not guessed at.
 * It comes from the document through the generated route table: naming a path
 * here would make a route added tomorrow wrong until somebody remembered this
 * line.
 */
export function expectedMediaOf(route: OperationRoute): string {
  return route.media;
}

/** Anything but an object is no input: the typed surface already refused it. */
export function isRawInput(value: unknown): value is RawInput {
  return typeof value === "object" && value !== null;
}
