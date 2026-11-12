import { buildTree, getProof } from "@tracetus/core";
import { describe, expect, it } from "vitest";
import {
  type VerifiableResponse,
  verifyProofOffline,
  verifyResponseOffline,
} from "../src/index.js";

const SCHEMA_ID = "tracetus:custody-event:1";

/**
 * Three leaves, written out rather than hashed from a record.
 *
 * A leaf is a 32-byte hash and nothing here depends on where it came from:
 * what is under test is the proof, which is the Merkle rule over whatever the
 * leaves are. Writing them keeps this suite to the hexadecimal and Merkle
 * modules, which are the two the published bundle carries — the record hash
 * is not in it, so asking for it here would have made it public code for the
 * sake of a fixture.
 */
const leaves = ["1a", "2b", "3c"].map((byte) => `0x${byte.repeat(32)}` as const);
const tree = buildTree(leaves);
const leaf = leaves[1] ?? leaves[0] ?? `0x${"00".repeat(32)}`;
const siblings = getProof(tree, 1);

function response(overrides: Partial<VerifiableResponse> = {}): VerifiableResponse {
  return {
    record: {
      id: `rec_${"0".repeat(32)}`,
      schemaId: SCHEMA_ID,
      recordHash: leaf,
      status: "anchored",
      createdAt: "2026-11-08T10:00:00.000Z",
    },
    proof: { leafIndex: 1, siblings, root: tree.root },
    batch: {
      id: `bat_${"0".repeat(32)}`,
      merkleRoot: tree.root,
      leafCount: 3,
      status: "confirmed",
      sealedAt: "2026-11-08T10:05:00.000Z",
    },
    ...overrides,
  };
}

describe("verifyProofOffline", () => {
  it("accepts the proof the tree produced", () => {
    expect(verifyProofOffline(leaf, siblings, tree.root)).toBe(true);
  });

  it("refuses a changed leaf, a changed root and a changed sibling", () => {
    const other = leaves[0] ?? leaf;

    expect(verifyProofOffline(other, siblings, tree.root)).toBe(false);
    expect(verifyProofOffline(leaf, siblings, `0x${"ff".repeat(32)}`)).toBe(false);
    expect(verifyProofOffline(leaf, [`0x${"ff".repeat(32)}`], tree.root)).toBe(false);
  });

  it("returns false instead of throwing for malformed hex", () => {
    expect(verifyProofOffline("not-hex", siblings, tree.root)).toBe(false);
    expect(verifyProofOffline(leaf, ["0xzz"], tree.root)).toBe(false);
    expect(verifyProofOffline(leaf, siblings, "0x")).toBe(false);
  });
});

describe("verifyResponseOffline", () => {
  it("checks a verification body against its batch root", () => {
    expect(verifyResponseOffline(response())).toBe(true);
  });

  it("is null while there is no proof or no root yet", () => {
    expect(verifyResponseOffline(response({ proof: null }))).toBeNull();
    expect(verifyResponseOffline(response({ batch: null }))).toBeNull();
    expect(
      verifyResponseOffline(
        response({
          batch: { id: "bat_x", merkleRoot: null, leafCount: 3, status: "open", sealedAt: null },
        }),
      ),
    ).toBeNull();
  });

  it("refuses a proof that names a root other than the batch root", () => {
    const body = response({ proof: { leafIndex: 1, siblings, root: `0x${"ee".repeat(32)}` } });

    expect(verifyResponseOffline(body)).toBe(false);
  });

  it("refuses a tampered record hash", () => {
    const body = response();
    const tampered = { ...body, record: { ...body.record, recordHash: `0x${"ee".repeat(32)}` } };

    expect(verifyResponseOffline(tampered)).toBe(false);
  });
});
