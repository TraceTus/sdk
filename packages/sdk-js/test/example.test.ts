/**
 * The example against a fake API: it issues, polls until the proof exists,
 * and checks the proof with the same Merkle rule as the core.
 */
import { hashPair } from "@tracetus/core";
/** The published entry, like the example itself: the two have to be one type. */
import { createTraceTusClient } from "@tracetus/sdk";
import { describe, expect, it } from "vitest";
import {
  ExampleError,
  describeOutcome,
  examplePayload,
  issueAndVerify,
  readOptions,
} from "../examples/issue-and-verify.js";

const BASE_URL = "https://api.example.test";
const RECORD_ID = `rec_${"0".repeat(32)}`;
const RECORD_HASH: `0x${string}` = `0x${"ab".repeat(32)}`;
const SIBLING: `0x${string}` = `0x${"cd".repeat(32)}`;
const ROOT = hashPair(RECORD_HASH, SIBLING);

const ISSUED = {
  envLabel: "simulation",
  record: {
    id: RECORD_ID,
    schemaId: "tracetus:custody-event:1",
    recordHash: RECORD_HASH,
    salt: "s".repeat(16),
    status: "pending",
    createdAt: "2026-11-10T10:00:00.000Z",
  },
};

function verifyBody(withProof: boolean) {
  return {
    envLabel: "simulation",
    proofValid: withProof ? true : null,
    record: {
      id: RECORD_ID,
      schemaId: "tracetus:custody-event:1",
      recordHash: RECORD_HASH,
      status: withProof ? "batched" : "pending",
      createdAt: "2026-11-10T10:00:00.000Z",
    },
    issuer: { legalName: "Emissor Exemplo Ltda", city: null, country: "BR" },
    batch: withProof
      ? {
          id: `bat_${"1".repeat(32)}`,
          merkleRoot: ROOT,
          leafCount: 2,
          status: "sealed",
          sealedAt: null,
        }
      : null,
    proof: withProof ? { leafIndex: 0, siblings: [SIBLING], root: ROOT } : null,
    anchors: [],
  };
}

interface FakeApi {
  fetch: typeof globalThis.fetch;
  requests: Request[];
}

/** Answers the issue, then `pendingPolls` verifies without proof, then one with. */
function fakeApi(pendingPolls: number, issueStatus = 201): FakeApi {
  const requests: Request[] = [];
  let polls = 0;
  const fetch: typeof globalThis.fetch = async (input, init) => {
    const request = new Request(input, init);

    requests.push(request);

    if (request.method === "POST") {
      const body =
        issueStatus === 201
          ? ISSUED
          : { envLabel: "simulation", error: { code: "SCHEMA_UNKNOWN", message: "x", issues: [] } };

      return Response.json(body, { status: issueStatus });
    }

    polls += 1;

    return Response.json(verifyBody(polls > pendingPolls));
  };

  return { fetch, requests };
}

const noWait = () => Promise.resolve();

describe("issueAndVerify", () => {
  it("issues, waits for the proof and finds it valid", async () => {
    const api = fakeApi(2);
    const client = createTraceTusClient({ baseUrl: BASE_URL, apiKey: "tk_x", fetch: api.fetch });

    const outcome = await issueAndVerify(client, { wait: noWait });

    expect(outcome).toEqual({
      envLabel: "simulation",
      recordId: RECORD_ID,
      recordHash: RECORD_HASH,
      proofValid: true,
      attempts: 3,
    });
    expect(api.requests.map((request) => request.method)).toEqual(["POST", "GET", "GET", "GET"]);
  });

  it("returns null proof when the batch stays open for every attempt", async () => {
    const api = fakeApi(100);
    const client = createTraceTusClient({ baseUrl: BASE_URL, apiKey: "tk_x", fetch: api.fetch });

    const outcome = await issueAndVerify(client, { wait: noWait, attempts: 3 });

    expect(outcome.proofValid).toBeNull();
    expect(outcome.attempts).toBe(3);
  });

  it("surfaces a refused issue as a typed error", async () => {
    const api = fakeApi(0, 422);
    const client = createTraceTusClient({ baseUrl: BASE_URL, apiKey: "tk_x", fetch: api.fetch });

    await expect(issueAndVerify(client, { wait: noWait })).rejects.toBeInstanceOf(ExampleError);
    await expect(issueAndVerify(client, { wait: noWait })).rejects.toMatchObject({
      code: "ISSUE_REFUSED",
    });
  });

  it("sends a payload made only of closed vocabulary", () => {
    const payload = examplePayload(new Date("2026-11-10T10:00:00Z"));

    expect(payload).toEqual({
      cte: "ORIGIN",
      subType: "ORI.HARVEST",
      occurredAt: "2026-11-10T10:00:00.000Z",
      lotRef: expect.stringMatching(/^lot-example-[0-9a-z]+$/),
      placeCode: "BR-5218805",
    });
  });
});

describe("readOptions", () => {
  it("defaults the URL to the local sandbox", () => {
    expect(readOptions({ TRACETUS_API_KEY: "tk_x" })).toEqual({
      baseUrl: "http://127.0.0.1:8787",
      apiKey: "tk_x",
    });
  });

  it("refuses to run without an issuer key", () => {
    expect(() => readOptions({})).toThrow(ExampleError);
  });
});

describe("describeOutcome", () => {
  it("says the batch is still open when there is no proof", () => {
    const text = describeOutcome({
      envLabel: "simulation",
      recordId: RECORD_ID,
      recordHash: RECORD_HASH,
      proofValid: null,
      attempts: 30,
    });

    expect(text).toContain("environment: simulation");
    expect(text).toContain("batch is still open");
  });

  it("says the proof is valid when it is", () => {
    const text = describeOutcome({
      envLabel: "testnet",
      recordId: RECORD_ID,
      recordHash: RECORD_HASH,
      proofValid: true,
      attempts: 2,
    });

    expect(text).toContain("proof valid after 2 polls");
  });
});
