import { createTraceTusClient } from "@tracetus/sdk";
/**
 * The built package in a real browser, with the browser's own `fetch`.
 *
 * Nothing is injected here, and that is the point: a client that captures
 * `globalThis.fetch` and calls it detached works on Node and fails in a
 * browser with "Illegal invocation", so no amount of Node testing would have
 * found it. Edge runtimes enforce the same rule.
 *
 * The requests go to the page's own origin, which the Vitest browser server
 * answers, so what is being tested is that a request leaves at all and that
 * its answer comes back as a value.
 */
import { describe, expect, it } from "vitest";

/** The page's origin: reachable, and answers something that is not our contract. */
const BASE_URL = globalThis.location.origin;

describe("the built client with the browser's own fetch", () => {
  it("sends a request and brings the answer back as a value", async () => {
    const tracetus = createTraceTusClient({ baseUrl: BASE_URL, allowInsecureBaseUrl: true });
    const { data, error, response } = await tracetus.verify.get({
      path: { id: `rec_${"0".repeat(32)}` },
    });

    /** Whatever the dev server answers, a request left the page. */
    expect(response).toBeDefined();
    expect([data, error].filter((part) => part !== undefined)).toHaveLength(1);
    expect(error?.code).not.toBe("CONNECTION_FAILED");
  });

  it("brings a refusal back as a typed error, not as an exception", async () => {
    const tracetus = createTraceTusClient({
      baseUrl: BASE_URL,
      apiKey: "tk_browser",
      allowInsecureBaseUrl: true,
      attempts: 1,
    });
    const { error } = await tracetus.records.create({
      body: { schemaId: "tracetus:custody-event:1", payload: {} },
    });

    expect(error).toBeDefined();
    expect(error?.code).not.toBe("CONNECTION_FAILED");
  });

  it("verifies a proof offline, with no call at all", async () => {
    const { verifyProofOffline } = await import("@tracetus/sdk");

    expect(verifyProofOffline("0x00", [], "0x00")).toBe(false);
  });
});

/**
 * What a browser does with a redirect, which is not what Node does.
 *
 * `redirect: "manual"` gives Node the `30x` itself; it gives a browser an
 * opaque response: status `0`, type `opaqueredirect`, no headers. Read as a
 * status that is neither a redirect nor a success, so without handling it the
 * one thing that happened — the API answered "look elsewhere" — came back as
 * `BAD_ANSWER`, which says something unknown answered. The path below is
 * answered with a `302` by this project's own server.
 */
describe("a redirect, as a browser reports it", () => {
  it("comes back as REDIRECTED and not as an unknown answer", async () => {
    const tracetus = createTraceTusClient({
      baseUrl: `${BASE_URL}/redirect-fixture`,
      apiKey: "tk_browser",
      allowInsecureBaseUrl: true,
      attempts: 3,
    });
    const { data, error } = await tracetus.records.create({
      body: { schemaId: "tracetus:custody-event:1", payload: {} },
    });

    expect(data).toBeUndefined();
    expect(error?.code).toBe("REDIRECTED");
    expect(error?.uncertain).toBe(false);
  });
});
