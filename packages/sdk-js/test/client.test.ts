/**
 * The client, against a `fetch` the test controls.
 *
 * What is asserted here is the promise a customer's developer relies on: the
 * methods are the API's operation names, a retry of a `POST` carries the key of
 * the first attempt, a failed request is a value, and the typed error carries
 * what a support conversation needs.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { createTraceTusClient } from "../src/client.js";
import { TraceTusUsageError } from "../src/errors.js";
import { fillPath } from "../src/request.js";
import type { ClientOptions } from "../src/settings.js";

const BASE_URL = "https://api.example.test";
const API_KEY = `tk_${"0".repeat(32)}_${"a".repeat(43)}`;
const RECORD_ID = `rec_${"0".repeat(32)}`;
const FIXED_KEY = "one-idempotency-key-for-every-attempt";
const SCHEMA_ID = "tracetus:custody-event:1";

const ISSUED = {
  envLabel: "simulation",
  record: {
    id: RECORD_ID,
    schemaId: SCHEMA_ID,
    recordHash: `0x${"ab".repeat(32)}`,
    salt: "s".repeat(16),
    status: "pending",
    createdAt: "2026-11-10T10:00:00.000Z",
  },
};

interface Answer {
  status: number;
  body?: unknown;
  /** Sent as it is, for an answer that is not the JSON it claims to be. */
  text?: string;
  headers?: Record<string, string>;
  /** Thrown instead of answered, as a dropped connection or an abort would be. */
  throws?: "TimeoutError" | "TypeError" | "AbortError";
}

interface Harness {
  requests: Request[];
  inits: RequestInit[];
  waits: number[];
  client: ReturnType<typeof createTraceTusClient>;
}

interface HarnessOptions extends Partial<ClientOptions> {
  /** The caller's own signal, so the fake can act like a real abort. */
  aborted?: AbortSignal;
}

/** Answers each call with the next entry, repeating the last one for ever. */
function harness(answers: readonly Answer[], options: HarnessOptions = {}): Harness {
  const requests: Request[] = [];
  const inits: RequestInit[] = [];
  const waits: number[] = [];
  const { aborted, ...clientOptions } = options;
  let at = 0;

  const fetchImpl: typeof globalThis.fetch = async (input, init) => {
    requests.push(new Request(input, init));
    inits.push(init ?? {});

    const answer = answers[Math.min(at, answers.length - 1)];

    at += 1;

    if (answer === undefined) {
      throw new Error("the harness has no answer to give");
    }

    if (answer.throws !== undefined) {
      const error = new Error(answer.throws);

      error.name = answer.throws;

      throw error;
    }

    const body = answer.text ?? (answer.body === undefined ? null : JSON.stringify(answer.body));

    return new Response(answer.status === 204 ? null : body, {
      status: answer.status,
      headers: { "content-type": "application/json", ...answer.headers },
    });
  };

  const client = createTraceTusClient({
    baseUrl: BASE_URL,
    apiKey: API_KEY,
    fetch: fetchImpl,
    sleep: async (milliseconds) => {
      waits.push(milliseconds);
    },
    random: () => 0.5,
    newIdempotencyKey: () => FIXED_KEY,
    ...clientOptions,
  });

  void aborted;

  return { requests, inits, waits, client };
}

afterEach(() => {
  vi.unstubAllEnvs();
});

function issueInput() {
  return { body: { schemaId: SCHEMA_ID, payload: { cte: "ORIGIN" } } };
}

describe("the methods are the API's operation names", () => {
  it("issues through records.create", async () => {
    const { client, requests } = harness([{ status: 201, body: ISSUED }]);
    const { data, error } = await client.records.create(issueInput());

    expect(error).toBeUndefined();
    expect(data?.record.id).toBe(RECORD_ID);
    expect(requests[0]?.url).toBe(`${BASE_URL}/v1/records`);
    expect(requests[0]?.method).toBe("POST");
  });

  it("issues many through records.createBatch", async () => {
    const { client, requests } = harness([
      { status: 201, body: { envLabel: "simulation", count: 1, records: [ISSUED.record] } },
    ]);

    await client.records.createBatch({
      body: { schemaId: SCHEMA_ID, records: [{ payload: { cte: "ORIGIN" } }] },
    });

    expect(requests[0]?.url).toBe(`${BASE_URL}/v1/records/batch`);
  });

  it("reads through records.get, with the route parameter in place", async () => {
    const { client, requests } = harness([{ status: 200, body: { envLabel: "simulation" } }]);

    await client.records.get({ path: { id: RECORD_ID } });

    expect(requests[0]?.url).toBe(`${BASE_URL}/v1/records/${RECORD_ID}`);
  });

  it("verifies through verify.get", async () => {
    const { client, requests } = harness([{ status: 200, body: { envLabel: "simulation" } }]);

    await client.verify.get({ path: { id: RECORD_ID } });

    expect(requests[0]?.url).toBe(`${BASE_URL}/v1/verify/${RECORD_ID}`);
  });

  it("asks the health check without any input at all", async () => {
    const { client, requests } = harness([{ status: 200, body: { status: "ok" } }]);

    await client.health.get();

    expect(requests[0]?.url).toBe(`${BASE_URL}/health`);
  });
});

describe("the key, the credential and the content type", () => {
  it("sends the API key as a bearer token", async () => {
    const { client, requests } = harness([{ status: 201, body: ISSUED }]);

    await client.records.create(issueInput());

    expect(requests[0]?.headers.get("authorization")).toBe(`Bearer ${API_KEY}`);
  });

  it("sends no credential when the key is empty, instead of an empty bearer", async () => {
    vi.stubEnv("TRACETUS_API_KEY", undefined);

    const { client, requests } = harness([{ status: 200, body: {} }], { apiKey: "" });

    await client.verify.get({ path: { id: RECORD_ID } });

    expect(requests[0]?.headers.get("authorization")).toBeNull();
  });

  it("makes an Idempotency-Key for a POST", async () => {
    const { client, requests } = harness([{ status: 201, body: ISSUED }]);

    await client.records.create(issueInput());

    expect(requests[0]?.headers.get("idempotency-key")).toBe(FIXED_KEY);
  });

  it("sends no Idempotency-Key on a read, which guards nothing", async () => {
    const { client, requests } = harness([{ status: 200, body: {} }]);

    await client.verify.get({ path: { id: RECORD_ID } });

    expect(requests[0]?.headers.get("idempotency-key")).toBeNull();
  });

  it("keeps a key the caller chose, so a derived key survives", async () => {
    const { client, requests } = harness([{ status: 201, body: ISSUED }]);

    await client.records.create({
      ...issueInput(),
      headers: { "Idempotency-Key": "caller-key-0123456789" },
    });

    expect(requests[0]?.headers.get("idempotency-key")).toBe("caller-key-0123456789");
  });

  it("declares a JSON body and sends it unchanged", async () => {
    const { client, requests } = harness([{ status: 201, body: ISSUED }]);

    await client.records.create(issueInput());

    expect(requests[0]?.headers.get("content-type")).toBe("application/json");
    expect(await requests[0]?.json()).toEqual(issueInput().body);
  });

  it("sends no content type on a request with no body", async () => {
    const { client, requests } = harness([{ status: 200, body: {} }]);

    await client.verify.get({ path: { id: RECORD_ID } });

    expect(requests[0]?.headers.get("content-type")).toBeNull();
  });

  it("adds the headers the client was built with", async () => {
    const { client, requests } = harness([{ status: 200, body: {} }], {
      headers: { "x-trace": "abc" },
    });

    await client.verify.get({ path: { id: RECORD_ID } });

    expect(requests[0]?.headers.get("x-trace")).toBe("abc");
  });
});

describe("a retry never issues twice", () => {
  it("makes one key per call, not one per attempt", async () => {
    let made = 0;
    const { client } = harness(
      [
        { status: 0, throws: "TimeoutError" },
        { status: 201, body: ISSUED },
      ],
      {
        newIdempotencyKey: () => {
          made += 1;

          return `key-${made.toString().padStart(16, "0")}`;
        },
      },
    );

    await client.records.create(issueInput());

    expect(made).toBe(1);
  });

  it("keeps the first key when a timeout is retried", async () => {
    const { client, requests } = harness([
      { status: 0, throws: "TimeoutError" },
      { status: 201, body: ISSUED },
    ]);

    const { data } = await client.records.create(issueInput());

    expect(data?.record.id).toBe(RECORD_ID);
    expect(requests).toHaveLength(2);
    expect(requests[1]?.headers.get("idempotency-key")).toBe(
      requests[0]?.headers.get("idempotency-key"),
    );
  });

  it("keeps the first key when a dropped connection is retried", async () => {
    const { client, requests } = harness([
      { status: 0, throws: "TypeError" },
      { status: 201, body: ISSUED },
    ]);

    await client.records.create(issueInput());

    expect(requests[1]?.headers.get("idempotency-key")).toBe(FIXED_KEY);
  });

  it("does not retry a POST answered 500", async () => {
    const { client, requests } = harness([
      { status: 500, body: { envLabel: "simulation", error: { code: "INTERNAL", message: "x" } } },
    ]);

    const { error } = await client.records.create(issueInput());

    expect(requests).toHaveLength(1);
    expect(error?.code).toBe("INTERNAL");
    expect(error?.attempts).toBe(1);
  });

  it("waits what Retry-After says on a 429 and then succeeds", async () => {
    const { client, waits, requests } = harness([
      {
        status: 429,
        headers: { "retry-after": "3" },
        body: { envLabel: "simulation", error: { code: "RATE_LIMITED", message: "x" } },
      },
      { status: 201, body: ISSUED },
    ]);

    const { data } = await client.records.create(issueInput());

    expect(waits).toEqual([3000]);
    expect(requests).toHaveLength(2);
    expect(data?.record.id).toBe(RECORD_ID);
  });

  it("waits what Retry-After says on a 503", async () => {
    const { client, waits } = harness([
      {
        status: 503,
        headers: { "retry-after": "1" },
        body: {
          envLabel: "simulation",
          error: { code: "IDEMPOTENCY_STORE_UNAVAILABLE", message: "x" },
        },
      },
      { status: 201, body: ISSUED },
    ]);

    await client.records.create(issueInput());

    expect(waits).toEqual([1000]);
  });

  it("gives up after the attempts it was given, and says how many it made", async () => {
    const { client, requests } = harness([{ status: 0, throws: "TypeError" }], { attempts: 2 });

    const { error } = await client.records.create(issueInput());

    expect(requests).toHaveLength(2);
    expect(error?.code).toBe("CONNECTION_FAILED");
    expect(error?.attempts).toBe(2);
  });

  it("makes exactly one attempt when built with one", async () => {
    const { client, requests } = harness([{ status: 0, throws: "TypeError" }], { attempts: 1 });

    await client.records.create(issueInput());

    expect(requests).toHaveLength(1);
  });

  it("takes the attempt count of the call over the client's", async () => {
    const { client, requests } = harness([{ status: 0, throws: "TypeError" }], { attempts: 5 });

    await client.records.create(issueInput(), { attempts: 2 });

    expect(requests).toHaveLength(2);
  });

  it("backs off with jitter when nothing answered and nothing asked for a wait", async () => {
    const { client, waits } = harness([{ status: 0, throws: "TypeError" }], { attempts: 3 });

    await client.records.create(issueInput());

    expect(waits).toEqual([125, 250]);
  });
});

describe("a failed request is a value", () => {
  it("does not throw when the API refuses", async () => {
    const { client } = harness([
      {
        status: 422,
        body: {
          envLabel: "simulation",
          error: {
            code: "PAYLOAD_PERSONAL_DATA",
            message: "the payload carries personal data",
            issues: [{ field: "payload.owner", code: "PERSONAL_CPF", detail: "looks like a CPF" }],
          },
        },
      },
    ]);

    const { data, error, response } = await client.records.create(issueInput());

    expect(data).toBeUndefined();
    expect(response?.status).toBe(422);
    expect(error).toMatchObject({
      code: "PAYLOAD_PERSONAL_DATA",
      status: 422,
      issues: [{ field: "payload.owner", code: "PERSONAL_CPF", detail: "looks like a CPF" }],
    });
  });

  it("does not throw when nothing answered", async () => {
    const { client } = harness([{ status: 0, throws: "TypeError" }], { attempts: 1 });
    const { data, error, response } = await client.records.create(issueInput());

    expect(data).toBeUndefined();
    expect(response).toBeUndefined();
    expect(error?.code).toBe("CONNECTION_FAILED");
    expect(error?.status).toBe(0);
  });

  it("tells a timeout from a dropped connection", async () => {
    const { client } = harness([{ status: 0, throws: "TimeoutError" }], { attempts: 1 });
    const { error } = await client.records.create(issueInput());

    expect(error?.code).toBe("TIMEOUT");
  });

  it("carries the request id, so a support thread has something to quote", async () => {
    const { client } = harness([
      {
        status: 404,
        headers: { "x-request-id": "req-123" },
        body: { envLabel: "simulation", error: { code: "RECORD_NOT_FOUND", message: "x" } },
      },
    ]);

    const { error } = await client.records.get({ path: { id: RECORD_ID } });

    expect(error?.requestId).toBe("req-123");
  });

  it("carries Retry-After, so a caller that stops knows how long to wait", async () => {
    const { client } = harness([
      {
        status: 429,
        headers: { "retry-after": "600" },
        body: { envLabel: "simulation", error: { code: "RATE_LIMITED", message: "x" } },
      },
    ]);

    const { error } = await client.records.create(issueInput());

    expect(error?.retryAfterSeconds).toBe(600);
  });

  it("names an answer outside the published contract instead of guessing", async () => {
    const { client } = harness([{ status: 418, body: { teapot: true } }]);
    const { error } = await client.records.create(issueInput());

    expect(error?.code).toBe("BAD_ANSWER");
    expect(error?.status).toBe(418);
  });
});

describe("how the client is built", () => {
  it("refuses an empty base URL instead of calling nothing", () => {
    expect(() => createTraceTusClient({ baseUrl: "" })).toThrow(TraceTusUsageError);
  });

  it("refuses an attempt count below one", () => {
    expect(() => createTraceTusClient({ baseUrl: BASE_URL, attempts: 0 })).toThrow(
      TraceTusUsageError,
    );
  });

  it("joins the base URL and the route without doubling the slash", async () => {
    const { client, requests } = harness([{ status: 200, body: {} }], { baseUrl: `${BASE_URL}/` });

    await client.verify.get({ path: { id: RECORD_ID } });

    expect(requests[0]?.url).toBe(`${BASE_URL}/v1/verify/${RECORD_ID}`);
  });

  it("keeps a path the base URL already carries", async () => {
    const { client, requests } = harness([{ status: 200, body: {} }], {
      baseUrl: `${BASE_URL}/gateway/`,
    });

    await client.verify.get({ path: { id: RECORD_ID } });

    expect(requests[0]?.url).toBe(`${BASE_URL}/gateway/v1/verify/${RECORD_ID}`);
  });

  it("escapes a route parameter instead of letting it change the path", async () => {
    const { client, requests } = harness([{ status: 200, body: {} }]);

    await client.verify.get({ path: { id: "../metrics" } });

    expect(requests[0]?.url).toBe(`${BASE_URL}/v1/verify/..%2Fmetrics`);
  });

  it("reads the key from TRACETUS_API_KEY when none was given", async () => {
    vi.stubEnv("TRACETUS_API_KEY", API_KEY);

    const { client, requests } = harness([{ status: 201, body: ISSUED }], { apiKey: undefined });

    await client.records.create(issueInput());

    expect(requests[0]?.headers.get("authorization")).toBe(`Bearer ${API_KEY}`);
  });
});

describe("an answer that is not JSON", () => {
  it("comes back as text, because that is what the route publishes", async () => {
    const { client } = harness([
      { status: 200, body: {}, headers: { "content-type": "text/plain" } },
    ]);
    const { data } = await client.metrics.get();

    expect(typeof data).toBe("string");
  });
});

describe("an answer the client cannot read", () => {
  it("says the request may have taken effect when a success is not readable JSON", async () => {
    const { client } = harness([
      { status: 201, text: "{ not json", headers: { "content-type": "application/json" } },
    ]);
    const { data, error } = await client.records.create(issueInput());

    expect(data).toBeUndefined();
    expect(error?.code).toBe("ANSWER_UNREADABLE");
    expect(error?.status).toBe(201);
    expect(error?.uncertain).toBe(true);
    expect(error?.message).toContain("may have taken effect");
  });

  it("carries the request id of an answer it could not read", async () => {
    const { client } = harness([
      {
        status: 201,
        text: "{ not json",
        headers: { "content-type": "application/json", "x-request-id": "req-9" },
      },
    ]);
    const { error } = await client.records.create(issueInput());

    expect(error?.requestId).toBe("req-9");
  });

  it("refuses a media type the route does not publish", async () => {
    const { client } = harness([
      { status: 201, text: "<html>proxy</html>", headers: { "content-type": "text/html" } },
    ]);
    const { data, error } = await client.records.create(issueInput());

    expect(data).toBeUndefined();
    expect(error?.code).toBe("ANSWER_UNREADABLE");
  });

  it("never answers with neither data nor error", async () => {
    const answers: Answer[] = [
      { status: 201, text: "{ not json", headers: { "content-type": "application/json" } },
      { status: 500, text: "oops", headers: { "content-type": "text/html" } },
      { status: 0, throws: "TypeError" },
    ];

    for (const answer of answers) {
      const { client } = harness([answer], { attempts: 1 });
      const result = await client.records.create(issueInput());

      expect([result.data, result.error].filter((part) => part !== undefined)).toHaveLength(1);
    }
  });

  it("marks a refusal the API answered as certain, because it did nothing", async () => {
    const { client } = harness([
      {
        status: 422,
        body: {
          envLabel: "simulation",
          error: { code: "PAYLOAD_INVALID", message: "x", issues: [] },
        },
      },
    ]);
    const { error } = await client.records.create(issueInput());

    expect(error?.uncertain).toBe(false);
  });
});

describe("an earlier attempt still being served", () => {
  const inProgress = {
    status: 409,
    body: {
      envLabel: "simulation",
      error: { code: "IDEMPOTENCY_KEY_IN_PROGRESS", message: "x", issues: [] },
    },
  };

  it("waits and asks again instead of giving up on a 409", async () => {
    const { client, requests, waits } = harness([inProgress, { status: 201, body: ISSUED }]);
    const { data } = await client.records.create(issueInput());

    expect(requests).toHaveLength(2);
    expect(waits).toHaveLength(1);
    expect(data?.record.id).toBe(RECORD_ID);
  });

  it("honours Retry-After while it waits", async () => {
    const { client, waits } = harness([
      { ...inProgress, headers: { "retry-after": "2" } },
      { status: 201, body: ISSUED },
    ]);

    await client.records.create(issueInput());

    expect(waits).toEqual([2000]);
  });

  it("says the outcome is unknown when the attempts run out", async () => {
    const { client } = harness([inProgress], { attempts: 2 });
    const { data, error } = await client.records.create(issueInput());

    expect(data).toBeUndefined();
    expect(error?.code).toBe("OUTCOME_UNKNOWN");
    expect(error?.uncertain).toBe(true);
    expect(error?.message).toContain("same Idempotency-Key");
  });

  it("still gives up at once on a 409 the client cannot wait out", async () => {
    const { client, requests } = harness([
      {
        status: 409,
        body: {
          envLabel: "simulation",
          error: { code: "DUPLICATE_RECORD", message: "x", issues: [] },
        },
      },
    ]);
    const { error } = await client.records.create(issueInput());

    expect(requests).toHaveLength(1);
    expect(error?.code).toBe("DUPLICATE_RECORD");
  });
});

describe("the caller's own abort", () => {
  it("ends the call at once, with its own code", async () => {
    const controller = new AbortController();
    const { client, requests } = harness([{ status: 0, throws: "AbortError" }], {
      aborted: controller.signal,
    });

    controller.abort();

    const { error } = await client.records.create(issueInput(), { signal: controller.signal });

    expect(error?.code).toBe("ABORTED");
    expect(error?.uncertain).toBe(false);
    expect(requests).toHaveLength(1);
  });

  it("is not retried, unlike a dropped connection", async () => {
    const controller = new AbortController();
    const { client, requests } = harness([{ status: 0, throws: "AbortError" }], {
      attempts: 5,
      aborted: controller.signal,
    });

    controller.abort();
    await client.records.create(issueInput(), { signal: controller.signal });

    expect(requests).toHaveLength(1);
  });

  it("interrupts a wait between attempts", async () => {
    const controller = new AbortController();
    const slept: number[] = [];
    const { client } = harness([{ status: 0, throws: "TypeError" }], {
      attempts: 5,
      sleep: async (milliseconds, signal) => {
        slept.push(milliseconds);
        controller.abort();

        expect(signal?.aborted).toBe(true);
      },
    });

    const { error } = await client.records.create(issueInput(), { signal: controller.signal });

    expect(slept).toHaveLength(1);
    expect(error?.code).toBe("ABORTED");
  });
});

describe("a redirect", () => {
  it("is not followed, so the key and the body stay where they were sent", async () => {
    const { client } = harness([
      { status: 307, text: "", headers: { location: "https://elsewhere.test/v1/records" } },
    ]);
    const { data, error } = await client.records.create(issueInput());

    expect(data).toBeUndefined();
    expect(error?.code).toBe("REDIRECTED");
  });

  it("asks fetch not to follow one", async () => {
    const { client, inits } = harness([{ status: 201, body: ISSUED }]);

    await client.records.create(issueInput());

    expect(inits[0]?.redirect).toBe("manual");
  });
});

describe("a header the caller writes in another casing", () => {
  it("replaces the client's own rather than arriving twice", async () => {
    const { client, requests } = harness([{ status: 201, body: ISSUED }]);

    await client.records.create({
      ...issueInput(),
      headers: { "idempotency-key": "caller-key-0123456789" },
    });

    expect(requests[0]?.headers.get("idempotency-key")).toBe("caller-key-0123456789");
  });

  it("lets the caller replace the credential too", async () => {
    const { client, requests } = harness([{ status: 201, body: ISSUED }]);

    await client.records.create({ ...issueInput(), headers: { Authorization: "Bearer other" } });

    expect(requests[0]?.headers.get("authorization")).toBe("Bearer other");
  });
});

describe("Retry-After in the forms HTTP allows", () => {
  it("waits the seconds a count names", async () => {
    const { client, waits } = harness([
      {
        status: 503,
        headers: { "retry-after": "4" },
        body: { envLabel: "simulation", error: { code: "x", message: "x", issues: [] } },
      },
      { status: 201, body: ISSUED },
    ]);

    await client.records.create(issueInput());

    expect(waits).toEqual([4000]);
  });

  it("waits until the instant a date names", async () => {
    const start = Date.parse("2026-11-11T12:00:00.000Z");
    const { client, waits } = harness(
      [
        {
          status: 503,
          headers: { "retry-after": "Wed, 11 Nov 2026 12:00:05 GMT" },
          body: { envLabel: "simulation", error: { code: "x", message: "x", issues: [] } },
        },
        { status: 201, body: ISSUED },
      ],
      { now: () => start },
    );

    await client.records.create(issueInput());

    expect(waits).toEqual([5000]);
  });

  it("ignores a value that is neither, instead of taking its digits", async () => {
    const { client, waits } = harness([
      {
        status: 503,
        headers: { "retry-after": "12abc" },
        body: { envLabel: "simulation", error: { code: "x", message: "x", issues: [] } },
      },
      { status: 201, body: ISSUED },
    ]);

    await client.records.create(issueInput());

    /** The backoff, not twelve seconds. */
    expect(waits).toEqual([125]);
  });

  it("ignores a fraction rather than rounding it", async () => {
    const { client, waits } = harness([
      {
        status: 503,
        headers: { "retry-after": "1.9" },
        body: { envLabel: "simulation", error: { code: "x", message: "x", issues: [] } },
      },
      { status: 201, body: ISSUED },
    ]);

    await client.records.create(issueInput());

    expect(waits).toEqual([125]);
  });

  it("treats a date already past as no wait at all", async () => {
    const { client, waits } = harness(
      [
        {
          status: 503,
          headers: { "retry-after": "Wed, 11 Nov 2026 11:59:00 GMT" },
          body: { envLabel: "simulation", error: { code: "x", message: "x", issues: [] } },
        },
        { status: 201, body: ISSUED },
      ],
      { now: () => Date.parse("2026-11-11T12:00:00.000Z") },
    );

    await client.records.create(issueInput());

    expect(waits).toEqual([0]);
  });
});

describe("what the client refuses to be built with", () => {
  const refused: [string, Partial<ClientOptions>, string][] = [
    ["no base URL", { baseUrl: "" }, "BASE_URL_MISSING"],
    ["a base URL that is not one", { baseUrl: "not a url" }, "BASE_URL_INVALID"],
    ["a base URL that is not http", { baseUrl: "ftp://api.example.test" }, "BASE_URL_INVALID"],
    ["plain http to another host", { baseUrl: "http://api.example.test" }, "BASE_URL_INSECURE"],
    ["an attempt count below one", { attempts: 0 }, "ATTEMPTS_INVALID"],
    ["a timeout of zero", { timeoutMs: 0 }, "TIMEOUT_INVALID"],
    ["a timeout that is not a number", { timeoutMs: Number.NaN }, "TIMEOUT_INVALID"],
  ];

  for (const [what, options, code] of refused) {
    it(`refuses ${what}, with a code`, () => {
      let caught: unknown;

      try {
        createTraceTusClient({ baseUrl: BASE_URL, ...options });
      } catch (error) {
        caught = error;
      }

      expect(caught).toBeInstanceOf(TraceTusUsageError);
      expect(caught instanceof TraceTusUsageError ? caught.code : "").toBe(code);
    });
  }

  it("allows plain http to this machine, where the demo runs", () => {
    expect(() => createTraceTusClient({ baseUrl: "http://127.0.0.1:8787" })).not.toThrow();
    expect(() => createTraceTusClient({ baseUrl: "http://localhost:8787" })).not.toThrow();
  });

  it("allows plain http elsewhere only when told to", () => {
    expect(() =>
      createTraceTusClient({ baseUrl: "http://api.example.test", allowInsecureBaseUrl: true }),
    ).not.toThrow();
  });

  it("refuses a body it cannot serialise, before any attempt", async () => {
    const { client, requests } = harness([{ status: 201, body: ISSUED }]);
    const circular: Record<string, unknown> = {};

    circular.self = circular;

    await expect(
      client.records.create({ body: { schemaId: SCHEMA_ID, payload: circular } }),
    ).rejects.toBeInstanceOf(TraceTusUsageError);
    expect(requests).toHaveLength(0);
  });

  /**
   * The type refuses a missing route parameter, and `test/types.test.ts` proves
   * that. This is the runtime half, for a caller with no types at all, and it
   * is asserted on the function that throws rather than through a cast.
   */
  it("refuses a route parameter the caller left out", () => {
    let caught: unknown;

    try {
      fillPath("/v1/records/{id}", {});
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(TraceTusUsageError);
    expect(caught instanceof TraceTusUsageError ? caught.code : "").toBe("PATH_PARAMETER_MISSING");
  });
});

/**
 * `uncertain` is the one field a caller reads before deciding whether to issue
 * again, so saying `false` where the truth is "nobody knows" is the dangerous
 * direction: the caller issues under a new key and writes twice.
 */
describe("whether a failed write may have taken effect", () => {
  const SERVER_FAILURES = [500, 502, 503, 504];

  for (const status of SERVER_FAILURES) {
    it(`says a POST answered ${status} may have taken effect`, async () => {
      const { client } = harness([
        { status, body: { error: { code: "INTERNAL", message: "internal error", issues: [] } } },
      ]);

      const { error } = await client.records.create(issueInput());

      expect(error?.uncertain).toBe(true);
      expect(error?.message).toContain("may have taken effect");
    });
  }

  it("says a POST answered by something outside the contract may have taken effect", async () => {
    const { client } = harness([{ status: 502, text: "<html>bad gateway</html>" }]);

    const { error } = await client.records.create(issueInput());

    expect(error?.code).toBe("BAD_ANSWER");
    expect(error?.uncertain).toBe(true);
  });

  it("says a POST refused for its content did not take effect", async () => {
    const { client } = harness([
      {
        status: 422,
        body: { error: { code: "PAYLOAD_INVALID", message: "payload invalid", issues: [] } },
      },
    ]);

    const { error } = await client.records.create(issueInput());

    expect(error?.code).toBe("PAYLOAD_INVALID");
    expect(error?.uncertain).toBe(false);
    expect(error?.message).not.toContain("may have taken effect");
  });

  it("says a failed read did not take effect, whatever answered it", async () => {
    const { client } = harness([{ status: 500, text: "<html>oops</html>" }]);

    const { error } = await client.records.get({ path: { id: RECORD_ID } });

    expect(error?.uncertain).toBe(false);
  });
});

describe("the wait between attempts", () => {
  it("backs off after a timeout instead of trying again at once", async () => {
    const { client, waits } = harness([{ status: 0, throws: "TimeoutError" }], {
      attempts: 3,
      timeoutMs: 1_000,
    });

    const { error } = await client.records.get({ path: { id: RECORD_ID } });

    expect(error?.code).toBe("TIMEOUT");
    expect(waits).toHaveLength(2);
    expect(waits.every((wait) => wait > 0)).toBe(true);
  });

  it("waits what Retry-After says, even when it is longer than one attempt's timeout", async () => {
    const { client, waits } = harness(
      [
        { status: 429, headers: { "retry-after": "3" }, body: {} },
        { status: 200, body: { envLabel: "simulation" } },
      ],
      { attempts: 3, timeoutMs: 1_000 },
    );

    await client.records.get({ path: { id: RECORD_ID } });

    expect(waits).toEqual([3_000]);
  });
});

describe("a redirect is one outcome, not a reason to try again", () => {
  it("spends a single attempt on it", async () => {
    const { client, requests } = harness(
      [{ status: 307, text: "", headers: { location: "https://elsewhere.test/v1/records" } }],
      { attempts: 3 },
    );

    const { error } = await client.records.create(issueInput());

    expect(error?.code).toBe("REDIRECTED");
    expect(requests).toHaveLength(1);
  });

  it("says why, so the reader knows it was a refusal to leak the key", async () => {
    const { client } = harness([
      { status: 302, text: "", headers: { location: "https://elsewhere.test/v1/records" } },
    ]);

    const { error } = await client.records.create(issueInput());

    expect(error?.message).toContain("does not follow redirects");
  });
});
