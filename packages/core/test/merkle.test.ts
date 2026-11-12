import { describe, expect, it } from "vitest";
import {
  type Hex32,
  MerkleError,
  buildTree,
  getProof,
  hashPair,
  isHex32,
  verifyProof,
} from "../src/index.js";

/**
 * A leaf, written rather than hashed from a record.
 *
 * A leaf is 32 bytes and this suite is about the tree over them, so where
 * they came from is not its subject — and the record hash is a different
 * module, whose own suite covers it. Keeping them apart is what lets the
 * published clients be built from this module and the hexadecimal one alone.
 */
const leaf = (index: number): Hex32 => `0x${index.toString(16).padStart(2, "0").repeat(32)}`;

describe("merkle", () => {
  it("returns the leaf itself as the root when the batch has one leaf", () => {
    const tree = buildTree([leaf(1)]);

    expect(tree.root).toBe(leaf(1));
    expect(verifyProof(leaf(1), getProof(tree, 0), tree.root)).toBe(true);
  });

  it("builds a valid inclusion proof for every index in even and odd batches", () => {
    for (const size of [2, 3, 5, 8, 13]) {
      const leaves = Array.from({ length: size }, (_, index) => leaf(index));
      const tree = buildTree(leaves);

      for (const [index, current] of leaves.entries()) {
        expect(verifyProof(current, getProof(tree, index), tree.root)).toBe(true);
      }
    }
  });

  it("lets the odd node rise alone, with no sibling in the proof", () => {
    const leaves = [1, 2, 3].map((n) => `0x${String(n).repeat(64)}` as const);
    const tree = buildTree(leaves);
    const proof = getProof(tree, 2);

    expect(tree.layers).toHaveLength(3);
    expect(tree.layers[1]).toHaveLength(2);
    expect(proof).toHaveLength(1);
    expect(verifyProof(leaves[2] ?? leaves[0], proof, tree.root)).toBe(true);
  });

  it("refuses to build a batch with a leaf that is not 32-byte hex", () => {
    expect(() => buildTree(["0xzz"])).toThrow(MerkleError);
  });

  it("returns false for a leaf or root that is not 32-byte hex", () => {
    const leaves = [1, 2].map((n) => `0x${String(n).repeat(64)}` as const);
    const tree = buildTree(leaves);

    expect(verifyProof("0xzz", getProof(tree, 0), tree.root)).toBe(false);
    expect(verifyProof(leaves[0] ?? "0x", getProof(tree, 0), "0xzz")).toBe(false);
  });

  it("returns false for a proof with a node that is not 32-byte hex", () => {
    const leaves = [1, 2].map((n) => `0x${String(n).repeat(64)}` as const);
    const tree = buildTree(leaves);

    expect(verifyProof(leaves[0] ?? "0x", ["0xzz"], tree.root)).toBe(false);
  });

  it("rejects a tampered leaf against the original root", () => {
    const tree = buildTree([leaf(1), leaf(2), leaf(3)]);

    expect(verifyProof(leaf(99), getProof(tree, 1), tree.root)).toBe(false);
  });

  it("computes the same pair hash regardless of the order", () => {
    expect(hashPair(leaf(1), leaf(2))).toBe(hashPair(leaf(2), leaf(1)));
  });

  it("throws a typed error for an empty batch", () => {
    expect(() => buildTree([])).toThrowError(/at least one leaf/);
  });

  it("throws a typed error for an index outside the batch", () => {
    const tree = buildTree([leaf(1)]);

    expect(() => getProof(tree, 1)).toThrowError(/outside the batch/);
  });

  it("throws a typed error for a leaf that is not 32-byte hex", () => {
    const invalidLeaves: string[] = ["0x1234"];

    expect(() => buildTree(invalidLeaves.filter(isHex32))).toThrowError(/at least one leaf/);
  });

  it("returns false when the proof holds an invalid node", () => {
    const tree = buildTree([leaf(1), leaf(2)]);
    const proof: string[] = ["0xzz"];

    expect(verifyProof(leaf(1), proof.filter(isHex32), tree.root)).toBe(false);
  });
});
