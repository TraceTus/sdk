/**
 * Both generated files must match the committed OpenAPI document. A stale
 * `src/generated/openapi.ts` or `src/generated/operations.ts` fails here, in
 * CI too: the SDK is generated and never edited by hand.
 *
 * The two halves have to agree with each other as well, because the client's
 * type comes from one and its runtime shape from the other: an operation in the
 * types with no route would be a method that throws, and a route with no types
 * would be a method nobody can call.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";
import { describe, expect, it } from "vitest";
import { OPERATIONS } from "../src/generated/operations.js";

const DOCUMENT = new URL("../../../apps/api/openapi.json", import.meta.url);
const COMMITTED = fileURLToPath(new URL("../src/generated/openapi.ts", import.meta.url));

interface DocumentResponse {
  content?: Record<string, unknown>;
}

interface DocumentOperation {
  operationId: string;
  responses?: Record<string, DocumentResponse>;
}

interface Document {
  paths: Record<string, Record<string, DocumentOperation>>;
}

function isDocument(value: unknown): value is Document {
  return typeof value === "object" && value !== null && "paths" in value;
}

function document(): Document {
  const parsed: unknown = JSON.parse(readFileSync(fileURLToPath(DOCUMENT), "utf8"));

  if (!isDocument(parsed)) {
    throw new Error("the OpenAPI document has no paths");
  }

  return parsed;
}

/**
 * The operation names the generated types declare. A key of the `operations`
 * interface is `resource.action`; a key of `paths` starts with a slash, so the
 * dot is what tells them apart.
 */
function typedOperationIds(): string[] {
  const source = readFileSync(COMMITTED, "utf8");

  return [...source.matchAll(/^ {4}"([a-z][a-zA-Z0-9]*\.[a-zA-Z0-9]+)": \{$/gm)].flatMap(
    (match) => match[1] ?? [],
  );
}

/** The CLI prefixes a comment the programmatic call does not; compare what follows it. */
function withoutHeader(text: string): string {
  return text.replace(/^\/\*\*[\s\S]*?\*\/\s*/, "");
}

describe("generated types", () => {
  it("match the committed OpenAPI document", async () => {
    const generated = astToString(await openapiTS(DOCUMENT));
    const committed = readFileSync(COMMITTED, "utf8");

    expect(withoutHeader(committed).trim()).toBe(generated.trim());
  });

  it("name every operation the document names", () => {
    const published = Object.values(document().paths).flatMap((item) =>
      Object.values(item).map((operation) => operation.operationId),
    );
    const typed = typedOperationIds();

    expect(published.length).toBeGreaterThan(0);

    for (const name of published) {
      expect(typed, `${name} is not in the generated types`).toContain(name);
    }
  });
});

/** What the document says a route answers on success, as the generator reads it. */
function successMediaOf(operation: DocumentOperation): string {
  for (const [status, response] of Object.entries(operation.responses ?? {})) {
    const code = Number(status);

    if (code >= 200 && code < 300) {
      const [media] = Object.keys(response.content ?? {});

      if (media !== undefined) {
        return media;
      }
    }
  }

  return "application/json";
}

describe("generated routes", () => {
  it("name every operation the document names, with its method, path and media", () => {
    const expected = Object.entries(document().paths).flatMap(([path, item]) =>
      Object.entries(item).map(([method, operation]) => [
        operation.operationId,
        { method: method.toUpperCase(), path, media: successMediaOf(operation) },
      ]),
    );

    expect(OPERATIONS).toEqual(Object.fromEntries(expected));
  });

  it("gives every route a method, a path and a media type", () => {
    for (const [id, route] of Object.entries(OPERATIONS)) {
      expect(route.method, id).toMatch(/^[A-Z]+$/);
      expect(route.path, id).toMatch(/^\//);
      expect(route.media, id).toMatch(/^[a-z]+\/[a-z+-]+$/);
    }
  });

  /**
   * The one route that does not answer JSON is the proof that this is read
   * from the document rather than assumed.
   */
  it("says text for the metrics route and JSON for the others", () => {
    expect(OPERATIONS["metrics.get"]?.media).toBe("text/plain");
    expect(OPERATIONS["records.create"]?.media).toBe("application/json");
  });

  it("has one route per operation named in the types", () => {
    expect(Object.keys(OPERATIONS).sort()).toEqual(typedOperationIds().sort());
  });
});
