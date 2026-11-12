/**
 * Issue one record and verify its inclusion proof offline, against a local
 * sandbox or any other installation. The only two things an integrator needs:
 * the API URL and an issuer key.
 *
 *   TRACETUS_API_URL=http://127.0.0.1:8787 TRACETUS_API_KEY=tk_... \
 *   pnpm --filter @tracetus/sdk example
 *
 * The proof exists once the worker seals the batch, so the script polls
 * `GET /v1/verify/{id}` for a while; `null` at the end means the batch was
 * still open, not that the record is wrong.
 */
import {
  type IssueRecordRequest,
  type TraceTusClient,
  type VerifyResponse,
  createTraceTusClient,
  verifyResponseOffline,
} from "@tracetus/sdk";

const DEFAULT_API_URL = "http://127.0.0.1:8787";
const DEFAULT_SCHEMA_ID = "tracetus:custody-event:1";
const DEFAULT_ATTEMPTS = 30;
const DEFAULT_INTERVAL_MS = 2000;
/** Rio Verde, Goiás: a locality code, never the name of a property. */
const PLACE_CODE = "BR-5218805";

export interface ExampleOptions {
  schemaId?: string;
  attempts?: number;
  /** Waits between polls; tests pass a no-op. */
  wait?: (milliseconds: number) => Promise<void>;
  intervalMs?: number;
}

export interface ExampleOutcome {
  envLabel: string;
  recordId: string;
  recordHash: string;
  /** `true` or `false` once the proof exists; `null` while the batch is open. */
  proofValid: boolean | null;
  attempts: number;
}

export type ExampleErrorCode = "ISSUE_REFUSED" | "VERIFY_REFUSED" | "MISSING_KEY";

/** Node runs this file with type stripping, so no parameter properties here. */
export class ExampleError extends Error {
  readonly code: ExampleErrorCode;

  constructor(code: ExampleErrorCode, message: string) {
    super(message);
    this.name = "ExampleError";
    this.code = code;
  }
}

/** A custody event with nothing but closed vocabulary: stage, sub-type, when, which lot, where. */
export function examplePayload(occurredAt: Date): IssueRecordRequest["payload"] {
  return {
    cte: "ORIGIN",
    subType: "ORI.HARVEST",
    occurredAt: occurredAt.toISOString(),
    lotRef: `lot-example-${occurredAt.getTime().toString(36)}`,
    placeCode: PLACE_CODE,
  };
}

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function pollVerify(
  client: TraceTusClient,
  recordId: string,
  options: Required<Pick<ExampleOptions, "attempts" | "wait" | "intervalMs">>,
): Promise<{ response: VerifyResponse; attempts: number }> {
  let last: VerifyResponse | undefined;

  for (let attempt = 1; attempt <= options.attempts; attempt += 1) {
    const verified = await client.verify.get({ path: { id: recordId } });

    if (verified.error !== undefined || verified.data === undefined) {
      throw new ExampleError("VERIFY_REFUSED", `verify refused: ${verified.error?.code ?? "?"}`);
    }

    last = verified.data;

    if (last.proof !== null) {
      return { response: last, attempts: attempt };
    }

    await options.wait(options.intervalMs);
  }

  if (last === undefined) {
    throw new ExampleError("VERIFY_REFUSED", "verify never answered");
  }

  return { response: last, attempts: options.attempts };
}

/** Issues one record, waits for its proof, checks the proof here. */
export async function issueAndVerify(
  client: TraceTusClient,
  options: ExampleOptions = {},
): Promise<ExampleOutcome> {
  /**
   * No idempotency key is written here: the client makes one for this call and
   * keeps it across every retry of it, so a timeout issues once.
   */
  const issued = await client.records.create({
    body: {
      schemaId: options.schemaId ?? DEFAULT_SCHEMA_ID,
      payload: examplePayload(new Date()),
    },
  });

  if (issued.error !== undefined || issued.data === undefined) {
    throw new ExampleError("ISSUE_REFUSED", `issue refused: ${issued.error?.code ?? "?"}`);
  }

  const { response, attempts } = await pollVerify(client, issued.data.record.id, {
    attempts: options.attempts ?? DEFAULT_ATTEMPTS,
    wait: options.wait ?? sleep,
    intervalMs: options.intervalMs ?? DEFAULT_INTERVAL_MS,
  });

  return {
    envLabel: response.envLabel,
    recordId: issued.data.record.id,
    recordHash: issued.data.record.recordHash,
    proofValid: verifyResponseOffline(response),
    attempts,
  };
}

export function readOptions(environment: Record<string, string | undefined>): {
  baseUrl: string;
  apiKey: string;
} {
  const apiKey = environment.TRACETUS_API_KEY;

  if (apiKey === undefined || apiKey === "") {
    throw new ExampleError("MISSING_KEY", "TRACETUS_API_KEY is required (an issuer key, tk_...)");
  }

  return { baseUrl: environment.TRACETUS_API_URL ?? DEFAULT_API_URL, apiKey };
}

export function describeOutcome(outcome: ExampleOutcome): string {
  const proof =
    outcome.proofValid === null
      ? `no proof yet after ${outcome.attempts} polls: the batch is still open`
      : `proof ${outcome.proofValid ? "valid" : "INVALID"} after ${outcome.attempts} polls`;

  return [
    `environment: ${outcome.envLabel}`,
    `record: ${outcome.recordId}`,
    `hash: ${outcome.recordHash}`,
    proof,
  ].join("\n");
}

async function main(): Promise<void> {
  const options = readOptions(process.env);
  const client = createTraceTusClient(options);
  const outcome = await issueAndVerify(client);

  process.stdout.write(`${describeOutcome(outcome)}\n`);
}

if (process.argv[1]?.endsWith("issue-and-verify.ts") === true) {
  await main();
}
