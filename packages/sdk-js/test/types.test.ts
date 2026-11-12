/**
 * What the compiler refuses.
 *
 * The client's types come from the generated document, so these are not tests
 * of hand-written signatures: they are the proof that the derivation works —
 * that a required body is required, that a route parameter cannot be left out,
 * that a misspelt method does not exist, and that the answer is the shape the
 * document publishes rather than `unknown`.
 *
 * A negative type assertion is the one place `@ts-expect-error` is allowed, and
 * only in a test.
 */
import { describe, expect, it } from "vitest";
import { createTraceTusClient } from "../src/client.js";
import type { DataOf, RequestInput, ResourceOf, TraceTusClient } from "../src/types.js";

const BASE_URL = "https://api.example.test";

/** Nothing is sent: these calls are only ever compiled. */
const client: TraceTusClient = createTraceTusClient({
  baseUrl: BASE_URL,
  fetch: async () => new Response("{}", { headers: { "content-type": "application/json" } }),
});

describe("the methods the document publishes", () => {
  it("has one namespace per resource and one method per action", () => {
    expect(typeof client.records.create).toBe("function");
    expect(typeof client.records.createBatch).toBe("function");
    expect(typeof client.records.get).toBe("function");
    expect(typeof client.verify.get).toBe("function");
    expect(typeof client.metrics.get).toBe("function");
    expect(typeof client.health.get).toBe("function");
  });

  it("has nothing the document does not publish", () => {
    // @ts-expect-error there is no records.delete in the API
    const missingAction = client.records.delete;
    // @ts-expect-error there is no batches namespace in the API
    const missingResource = client.batches;

    expect(missingAction).toBeUndefined();
    expect(missingResource).toBeUndefined();
  });
});

/**
 * A refusal is only ever compiled, never called: the assertion is the
 * `@ts-expect-error` above it, and calling would start a request nobody awaits.
 */
describe("what a call requires", () => {
  it("refuses an issuance with no body", () => {
    // @ts-expect-error records.create needs a body
    const refused = () => client.records.create();

    expect(typeof refused).toBe("function");
  });

  it("refuses a read with no route parameter", () => {
    // @ts-expect-error records.get needs the id in the path
    const refused = () => client.records.get({});

    expect(typeof refused).toBe("function");
  });

  it("refuses a body the schema envelope does not declare", () => {
    const refused = () =>
      client.records.create({
        // @ts-expect-error schemaId is required by the envelope
        body: { payload: {} },
      });

    expect(typeof refused).toBe("function");
  });

  it("refuses a body on a route that takes none", () => {
    // @ts-expect-error verify.get takes no body
    const refused = () => client.verify.get({ path: { id: "rec_x" }, body: {} });

    expect(typeof refused).toBe("function");
  });

  it("asks for no input at all where the route takes none", async () => {
    expect((await client.health.get()).error).toBeUndefined();
    expect((await client.metrics.get()).error).toBeUndefined();
  });
});

describe("what a call gives back", () => {
  it("types the answer as the document publishes it", async () => {
    const { data } = await client.verify.get({ path: { id: `rec_${"0".repeat(32)}` } });

    /** `proofValid` exists on the verification answer and nowhere else. */
    expect(data?.proofValid).toBeUndefined();
  });

  it("types a text route as text", () => {
    const text: DataOf<"metrics.get"> = "# HELP";

    expect(text).toBe("# HELP");
  });

  it("derives the resource from the operation name", () => {
    const resource: ResourceOf<"records.create"> = "records";

    expect(resource).toBe("records");
  });

  it("derives the input of an operation from the document", () => {
    const input: RequestInput<"records.get"> = { path: { id: `rec_${"0".repeat(32)}` } };

    expect(input.path.id).toMatch(/^rec_/);
  });
});

/**
 * A route whose whole query is optional is the case that is easy to get
 * wrong: the document declares parameters, so a naive type asks for
 * `query: {}` on a call that needs nothing.
 */
describe("a query that is entirely optional", () => {
  it("is left out altogether", async () => {
    expect((await client.privateContent.list()).error).toBeUndefined();
  });

  it("is still accepted when the caller has a cursor", async () => {
    expect((await client.privateContent.list({ query: { limit: 10 } })).error).toBeUndefined();
  });

  it("refuses a query key the document does not publish", () => {
    // @ts-expect-error there is no `page` parameter on this route
    const refused = () => client.privateContent.list({ query: { page: 2 } });

    expect(typeof refused).toBe("function");
  });
});
