/**
 * Binary Merkle tree over keccak256, without I/O.
 *
 * Rules of the network we anchor on: a record is a leaf; a transaction on the
 * network is a batch (the root). The inclusion proof lets anyone check a leaf
 * against the root written to the network without depending on TraceTus.
 *
 * Conventions:
 * - Leaves are already 32-byte hashes (the record hash), never the content.
 * - Pairs are ordered (smaller first) before concatenating, so that the proof
 *   does not have to carry a position. Simple to verify in Solidity.
 * - Odd number of nodes: the last one is promoted without being duplicated
 *   (this avoids the classic leaf-duplication ambiguity).
 */
import { keccak_256 } from "@noble/hashes/sha3";
import { type Hex32, bytesToHex32, compareBytes, hex32ToBytes, isHex32 } from "./hex.js";

const BYTES_IN_HASH = 32;
const PAIR_LENGTH = BYTES_IN_HASH * 2;

export type { Hex32 } from "./hex.js";
export { isHex32 } from "./hex.js";

export function hashPair(a: Hex32, b: Hex32): Hex32 {
  const x = hex32ToBytes(a);
  const y = hex32ToBytes(b);
  const [left, right] = compareBytes(x, y) <= 0 ? [x, y] : [y, x];
  const pair = new Uint8Array(PAIR_LENGTH);

  pair.set(left, 0);
  pair.set(right, BYTES_IN_HASH);

  return bytesToHex32(keccak_256(pair));
}

export interface MerkleTree {
  root: Hex32;
  leaves: Hex32[];
  layers: Hex32[][];
}

/** Pairs left to right; an odd node at the end is carried up as it is. */
function nextLayer(layer: readonly Hex32[]): Hex32[] {
  const next: Hex32[] = [];

  for (const [position, left] of layer.entries()) {
    if (position % 2 === 1) {
      continue;
    }

    const right = layer[position + 1];

    next.push(right === undefined ? left : hashPair(left, right));
  }

  return next;
}

/** The single node of the last layer; `reduce` keeps the type without a guard. */
function lastNode(layer: readonly Hex32[], fallback: Hex32): Hex32 {
  return layer.reduce((_, node) => node, fallback);
}

export function buildTree(leaves: Hex32[]): MerkleTree {
  const first = leaves[0];

  if (first === undefined) {
    throw new MerkleError("EMPTY_TREE", "a batch needs at least one leaf");
  }

  for (const leaf of leaves) {
    if (!isHex32(leaf)) {
      throw new MerkleError("BAD_LEAF", `invalid leaf: ${leaf}`);
    }
  }

  let current: Hex32[] = [...leaves];
  const layers: Hex32[][] = [current];

  while (current.length > 1) {
    current = nextLayer(current);
    layers.push(current);
  }

  return { root: lastNode(current, first), leaves: [...leaves], layers };
}

export function getProof(tree: MerkleTree, index: number): Hex32[] {
  if (index < 0 || index >= tree.leaves.length) {
    throw new MerkleError("BAD_INDEX", `index outside the batch: ${index}`);
  }

  const proof: Hex32[] = [];
  let position = index;

  for (const layer of tree.layers.slice(0, -1)) {
    const siblingIndex = position % 2 === 0 ? position + 1 : position - 1;
    const sibling = layer[siblingIndex];

    if (sibling !== undefined) {
      proof.push(sibling);
    }

    position = Math.floor(position / 2);
  }

  return proof;
}

/** Pure verification: what the public verifier runs in the browser. */
export function verifyProof(leaf: Hex32, proof: Hex32[], root: Hex32): boolean {
  if (!isHex32(leaf) || !isHex32(root)) {
    return false;
  }

  let accumulator = leaf;

  for (const node of proof) {
    if (!isHex32(node)) {
      return false;
    }

    accumulator = hashPair(accumulator, node);
  }

  return accumulator === root;
}

export class MerkleError extends Error {
  constructor(
    public readonly code: "EMPTY_TREE" | "BAD_LEAF" | "BAD_INDEX",
    message: string,
  ) {
    super(message);
    this.name = "MerkleError";
  }
}
