/**
 * Regenerates everything in `src/generated` from `apps/api/openapi.json`.
 *
 * Two files come out of the one document, and neither is ever edited by hand:
 *
 * - `openapi.ts`, the types, through openapi-typescript. Its `operations`
 *   interface is keyed by `operationId`, which is what lets the client be typed
 *   without a line per endpoint.
 * - `operations.ts`, the same names at runtime: a client has to know which
 *   method, which path and which media type an `operationId` means, and a type
 *   cannot say that once the program is running.
 *
 * `test/generated.test.ts` refuses a stale copy of either.
 */
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const DOCUMENT = fileURLToPath(new URL("../../../apps/api/openapi.json", import.meta.url));
const TYPES_TARGET = fileURLToPath(new URL("../src/generated/openapi.ts", import.meta.url));
const OPERATIONS_TARGET = fileURLToPath(new URL("../src/generated/operations.ts", import.meta.url));

const HEADER = `/**
 * Generated from apps/api/openapi.json. Do not edit by hand: run
 * \`pnpm --filter @tracetus/sdk generate\`.
 *
 * Which method and which path each operation name means. The types in
 * \`openapi.ts\` say what goes in and what comes out; this says where to send it.
 */
`;

interface Operation {
  method: string;
  path: string;
  /** The media type this route answers on success, as the document declares it. */
  media: string;
}

const JSON_MEDIA_TYPE = "application/json";
const SUCCESS_FLOOR = 200;
const SUCCESS_CEILING = 300;

/**
 * What this script refuses, with a code, like every error of this repository
 * as every error of this repository does. Each one says the document is not what the
 * generator can read, which is a contract bug rather than a mistake of whoever
 * ran the command: the API's own contract test refuses all three before the
 * document is ever committed.
 */
type GenerateErrorCode = "NO_PATHS" | "BAD_PATHS" | "NO_OPERATION_ID";

class GenerateError extends Error {
  /**
   * Assigned in the body rather than declared as a parameter property, because
   * this script runs under `node --experimental-strip-types`, which only
   * removes types and cannot generate the assignment one implies.
   */
  readonly code: GenerateErrorCode;

  constructor(code: GenerateErrorCode, message: string) {
    super(message);
    this.code = code;
    this.name = "GenerateError";
  }
}

function readOperations(): Record<string, Operation> {
  const document: unknown = JSON.parse(readFileSync(DOCUMENT, "utf8"));

  if (typeof document !== "object" || document === null || !("paths" in document)) {
    throw new GenerateError("NO_PATHS", "the OpenAPI document has no paths");
  }

  const { paths } = document;

  if (typeof paths !== "object" || paths === null) {
    throw new GenerateError("BAD_PATHS", "the OpenAPI document's paths is not an object");
  }

  const found: Record<string, Operation> = {};

  for (const [path, item] of Object.entries(paths)) {
    if (typeof item !== "object" || item === null) {
      continue;
    }

    for (const [method, operation] of Object.entries(item)) {
      found[operationIdOf(operation, method, path)] = {
        method: method.toUpperCase(),
        path,
        media: successMediaOf(operation),
      };
    }
  }

  return found;
}

/** A route without a name is a contract bug, and the API's own test refuses it. */
function operationIdOf(operation: unknown, method: string, path: string): string {
  if (typeof operation !== "object" || operation === null || !("operationId" in operation)) {
    throw new GenerateError(
      "NO_OPERATION_ID",
      `${method.toUpperCase()} ${path} has no operationId`,
    );
  }

  const { operationId } = operation;

  if (typeof operationId !== "string" || operationId === "") {
    throw new GenerateError(
      "NO_OPERATION_ID",
      `${method.toUpperCase()} ${path} has an empty operationId`,
    );
  }

  return operationId;
}

/**
 * What a route answers on success, read from the document rather than guessed
 * at. `GET /v1/metrics` answers `text/plain` and every other route answers
 * JSON, and the client has to know which without naming a path: a route added
 * tomorrow with a media type of its own is then right by regeneration instead
 * of by somebody remembering.
 */
function successMediaOf(operation: unknown): string {
  if (typeof operation !== "object" || operation === null || !("responses" in operation)) {
    return JSON_MEDIA_TYPE;
  }

  const { responses } = operation;

  if (typeof responses !== "object" || responses === null) {
    return JSON_MEDIA_TYPE;
  }

  for (const [status, response] of Object.entries(responses)) {
    const code = Number(status);

    if (!Number.isInteger(code) || code < SUCCESS_FLOOR || code >= SUCCESS_CEILING) {
      continue;
    }

    const media = mediaOf(response);

    if (media !== undefined) {
      return media;
    }
  }

  return JSON_MEDIA_TYPE;
}

function mediaOf(response: unknown): string | undefined {
  if (typeof response !== "object" || response === null || !("content" in response)) {
    return undefined;
  }

  const { content } = response;

  if (typeof content !== "object" || content === null) {
    return undefined;
  }

  const [media] = Object.keys(content);

  return media;
}

function render(operations: Record<string, Operation>): string {
  const entries = Object.entries(operations)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(
      ([id, { method, path, media }]) =>
        `  "${id}": { method: "${method}", path: "${path}", media: "${media}" },`,
    )
    .join("\n");

  return `${HEADER}
export interface OperationRoute {
  method: string;
  path: string;
  /** What the route answers on success, from the document. */
  media: string;
}

export const OPERATIONS: Readonly<Record<string, OperationRoute>> = {
${entries}
};
`;
}

execFileSync("openapi-typescript", [DOCUMENT, "-o", TYPES_TARGET], { stdio: "inherit" });
writeFileSync(OPERATIONS_TARGET, render(readOperations()));

process.stdout.write(`${TYPES_TARGET}\n${OPERATIONS_TARGET}\n`);
