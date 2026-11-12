# @tracetus/core

The part of the TraceTus domain package the published clients are built from:
hexadecimal encoding and the Merkle rule.

It is not published to a registry and it is not an API to depend on. It is here
because `@tracetus/sdk` imports it rather than restating the Merkle rule — the
code that builds an inclusion proof on the platform is the code that checks it
in the client — and because a reader of this repository should be able to see
that rule rather than take it on trust. The build bundles it in, which is why
the published package has no runtime dependency of ours.

The full domain package lives in TraceTus's monorepo, where it is changed. What
is mirrored here is two modules and their suites — the two whose code the
published bundle actually carries, and no more than that:

- `src/hex.ts` — a 32-byte value as `0x…`, and byte comparison.
- `src/merkle.ts` — the leaf hash, the pair hash, the tree, the proof, and the
  verification of a proof.

`src/index.ts` is written when this repository is built and names those two.

The rule, in one paragraph. A record is a leaf and a batch is one transaction
carrying one Merkle root. A leaf is the record hash, which the API computes:
`keccak256` over a canonical form of the record, with a salt, so that a
payload cannot be guessed back out of it — a client never has to recompute it,
and the code that does is not here. A pair is `keccak256` of its two children
with the smaller one first, so a proof carries no left-or-right flag and is
cheap to check in Solidity. A level with an odd number of nodes carries the
last one up unchanged rather than duplicating it, which is the classic
ambiguity. Checking a proof needs only the pair rule, which is why only the
pair rule is here.

```bash
pnpm --filter @tracetus/core test     # 100% of this package, or it fails
```
