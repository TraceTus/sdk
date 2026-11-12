/**
 * Packs the package and installs it into an empty project, the way a customer
 * does, then issues a record against a server that answers like the API.
 *
 * This is the only check that exercises what npm would actually publish: the
 * `files` list, the `exports` map, the declarations, and both module formats.
 * A build that works from source and breaks once installed is exactly the
 * failure this catches, and no unit test can.
 *
 *   pnpm --filter @tracetus/sdk smoke
 */
import { execFile } from "node:child_process";
import { mkdtempSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const PACKAGE_ROOT = fileURLToPath(new URL("..", import.meta.url));
const RECORD_ID = `rec_${"0".repeat(32)}`;
const CREATED = 201;

const ISSUED = {
  envLabel: "simulation",
  record: {
    id: RECORD_ID,
    schemaId: "tracetus:custody-event:1",
    recordHash: `0x${"ab".repeat(32)}`,
    salt: "s".repeat(16),
    status: "pending",
    createdAt: "2026-11-10T10:00:00.000Z",
  },
};

interface Received {
  idempotencyKey: string | undefined;
  authorization: string | undefined;
  url: string | undefined;
}

const received: Received = { idempotencyKey: undefined, authorization: undefined, url: undefined };

const runAsync = promisify(execFile);

/**
 * Asynchronous on purpose: the server that answers these programs lives in this
 * same process, so a synchronous child would block the event loop and every
 * request would time out.
 */
async function run(command: string, args: readonly string[], cwd: string): Promise<string> {
  const { stdout } = await runAsync(command, [...args], { cwd, encoding: "utf8" });

  return stdout;
}

/** Answers one issuance, like `POST /v1/records` does. */
function startApi(): Promise<{ url: string; close: () => void }> {
  const server = createServer((request, response) => {
    received.idempotencyKey = headerOf(request.headers["idempotency-key"]);
    received.authorization = headerOf(request.headers.authorization);
    received.url = request.url;

    response.writeHead(CREATED, { "content-type": "application/json" });
    response.end(JSON.stringify(ISSUED));
  });

  return new Promise((ready) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address !== null ? address.port : 0;

      ready({ url: `http://127.0.0.1:${port}`, close: () => server.close() });
    });
  });
}

type SmokeErrorCode = "NO_TARBALL" | "WRONG_ANSWER" | "NO_IDEMPOTENCY_KEY" | "CONSUMER_REFUSED";

/**
 * Every failure of this script carries a code, like every other error here.
 * The field is declared and assigned rather than written as a parameter
 * property: this file runs under `--experimental-strip-types`, which strips
 * types and does not transform syntax.
 */
class SmokeError extends Error {
  readonly code: SmokeErrorCode;

  constructor(code: SmokeErrorCode, message: string) {
    super(message);
    this.name = "SmokeError";
    this.code = code;
  }
}

function headerOf(value: string | string[] | undefined): string | undefined {
  return typeof value === "string" ? value : undefined;
}

/**
 * What the throwaway consumer throws. A consumer's only job is to exit
 * non-zero, and it carries a code for the same reason everything else here
 * does: the output says which check failed without being read line by line.
 */
const CONSUMER_FAILURE = `
class ConsumerFailure extends Error {
  constructor(code, message) {
    super(message);
    this.name = "ConsumerFailure";
    this.code = code;
  }
}
`;

const ESM_PROGRAM = `
import { createTraceTusClient, verifyProofOffline } from "@tracetus/sdk";
${CONSUMER_FAILURE}

const tracetus = createTraceTusClient({ baseUrl: process.argv[2], apiKey: "tk_smoke" });
const { data, error } = await tracetus.records.create({
  body: { schemaId: "tracetus:custody-event:1", payload: { cte: "ORIGIN" } },
});

if (error !== undefined) {
  throw new ConsumerFailure("CLIENT_REFUSED", \`the client refused: \${error.code}\`);
}

if (verifyProofOffline("0x00", [], "0x00") !== false) {
  throw new ConsumerFailure("BAD_HEX_VERIFIED", "malformed hex should not verify");
}

process.stdout.write(data.record.id);
`;

const CJS_PROGRAM = `
const { createTraceTusClient } = require("@tracetus/sdk");
${CONSUMER_FAILURE}

async function main() {
  const tracetus = createTraceTusClient({ baseUrl: process.argv[2], apiKey: "tk_smoke" });
  const { data, error } = await tracetus.records.create({
    body: { schemaId: "tracetus:custody-event:1", payload: { cte: "ORIGIN" } },
  });

  if (error !== undefined) {
    throw new ConsumerFailure("CLIENT_REFUSED", "the client refused: " + error.code);
  }

  process.stdout.write(data.record.id);
}

main();
`;

/**
 * Declarations are part of the package, so a type error here fails the smoke
 * test. It is written the way the documentation tells a customer to write it:
 * check `error`, and `data` is defined afterwards without a cast or a `?.`.
 */
const TYPED_PROGRAM = `
import { createTraceTusClient } from "@tracetus/sdk";

class ConsumerFailure extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "ConsumerFailure";
    this.code = code;
  }
}

const tracetus = createTraceTusClient({ baseUrl: "https://api.example.test" });

export async function issue(): Promise<string> {
  const { data, error } = await tracetus.records.create({
    body: { schemaId: "tracetus:custody-event:1", payload: {} },
  });

  if (error !== undefined) {
    throw new ConsumerFailure("CLIENT_REFUSED", error.code);
  }

  return data.record.id;
}
`;

async function packed(): Promise<string> {
  await run("npm", ["pack", "--pack-destination", PACKAGE_ROOT], PACKAGE_ROOT);

  const tarball = readdirSync(PACKAGE_ROOT).find((name) => name.endsWith(".tgz"));

  if (tarball === undefined) {
    throw new SmokeError("NO_TARBALL", "npm pack produced no tarball");
  }

  return join(PACKAGE_ROOT, tarball);
}

async function prepareProject(directory: string, tarball: string): Promise<void> {
  writeFileSync(
    join(directory, "package.json"),
    JSON.stringify({ name: "smoke", private: true, version: "0.0.0", type: "module" }, null, 2),
  );
  writeFileSync(join(directory, "esm.mjs"), ESM_PROGRAM);
  writeFileSync(join(directory, "cjs.cjs"), CJS_PROGRAM);
  writeFileSync(join(directory, "typed.ts"), TYPED_PROGRAM);
  /** A `.cts` file resolves through the `require` condition, which is the point. */
  writeFileSync(join(directory, "typed-cjs.cts"), TYPED_PROGRAM);
  /**
   * Two compilations, because a package with one `types` entry for both
   * conditions compiles under `nodenext` and fails under `node16` with
   * `require`: the declaration it finds is the ESM one. A CommonJS consumer is
   * exactly who would hit that, so one is compiled here.
   */
  writeFileSync(join(directory, "tsconfig.json"), JSON.stringify(tsconfigFor("nodenext"), null, 2));
  writeFileSync(
    join(directory, "tsconfig.cjs.json"),
    JSON.stringify(tsconfigFor("node16", "typed-cjs.cts"), null, 2),
  );
  await run("npm", ["install", "--no-audit", "--no-fund", tarball], directory);
}

function tsconfigFor(module: string, file = "typed.ts") {
  return {
    compilerOptions: {
      module,
      moduleResolution: module,
      target: "es2022",
      strict: true,
      noEmit: true,
      skipLibCheck: false,
      types: [],
    },
    include: [file],
  };
}

function assertSame(what: string, found: string, wanted: string): void {
  if (found !== wanted) {
    throw new SmokeError("WRONG_ANSWER", `${what}: expected ${wanted}, found ${found}`);
  }
}

const tarball = await packed();
const directory = mkdtempSync(join(tmpdir(), "tracetus-sdk-smoke-"));
const api = await startApi();

try {
  await prepareProject(directory, tarball);

  assertSame("ESM", await run("node", ["esm.mjs", api.url], directory), RECORD_ID);
  assertSame("the route called", received.url ?? "", "/v1/records");
  assertSame("the credential sent", received.authorization ?? "", "Bearer tk_smoke");

  if (received.idempotencyKey === undefined) {
    throw new SmokeError("NO_IDEMPOTENCY_KEY", "the client sent no Idempotency-Key");
  }

  assertSame("CJS", await run("node", ["cjs.cjs", api.url], directory), RECORD_ID);
  await run("node", [typescriptCompiler(), "-p", "tsconfig.json"], directory);
  await run("node", [typescriptCompiler(), "-p", "tsconfig.cjs.json"], directory);

  process.stdout.write(
    "smoke: ESM, CommonJS and the declarations all work from the tarball, under nodenext and node16\n",
  );
} finally {
  api.close();
  rmSync(directory, { recursive: true, force: true });
  rmSync(tarball, { force: true });
}

/**
 * The repository's own TypeScript, so the check matches what we build with and
 * needs no network. Module resolution follows the file being compiled, so it
 * still reads `@tracetus/sdk` out of the temporary project.
 */
function typescriptCompiler(): string {
  return createRequire(import.meta.url).resolve("typescript/bin/tsc");
}
