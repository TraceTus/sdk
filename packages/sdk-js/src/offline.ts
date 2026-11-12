/**
 * Checking an inclusion proof without asking anybody.
 *
 * This is the point of a proof: whoever holds one checks it against the batch
 * root with nothing but arithmetic, and the API being down or lying changes
 * nothing. The Merkle rule is `@tracetus/core`'s, the same code the platform
 * uses to build the proof, bundled into this package so a customer installs one
 * thing and no dependency.
 */
import { isHex32, verifyProof } from "@tracetus/core";
import type { components } from "./generated/openapi.js";

/**
 * Pure Merkle check: the record hash is the leaf, the siblings climb to the
 * root. Malformed hex is `false`, never an exception.
 */
export function verifyProofOffline(
  recordHash: string,
  siblings: readonly string[],
  root: string,
): boolean {
  if (!isHex32(recordHash) || !isHex32(root) || !siblings.every(isHex32)) {
    return false;
  }

  return verifyProof(recordHash, [...siblings], root);
}

type Verifiable = "record" | "proof" | "batch";

/**
 * What either answer that carries a proof looks like, taken from the generated
 * document rather than described here: the public verification and the issuer's
 * own read of a record both carry the three fields this needs.
 */
export type VerifiableResponse =
  | Pick<components["schemas"]["VerifyResponse"], Verifiable>
  | Pick<components["schemas"]["RecordDetail"], Verifiable>;

/**
 * The same check over the body of `verify.get` or `records.get`. `null` while
 * the record has no proof or its batch has no root yet; the proof has to name
 * the batch root it claims to reach.
 */
export function verifyResponseOffline(response: VerifiableResponse): boolean | null {
  const proof = response.proof;
  const root = response.batch?.merkleRoot ?? null;

  if (proof === null || root === null) {
    return null;
  }

  return (
    proof.root === root && verifyProofOffline(response.record.recordHash, proof.siblings, root)
  );
}
