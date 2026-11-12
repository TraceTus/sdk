# Security

## Reporting a vulnerability

Write to **security@tracetus.com**. You get an answer within **2 business
days**.

**Do not open a public issue**, and do not post it anywhere else first. If you
need to encrypt the report, say so in a first message with no detail in it and
you will be sent a key.

Tell us, as far as you know it: what the problem is, which package and version,
how to reproduce it, and what an attacker gets out of it. A proof of concept
helps and is not required.

What you can expect:

1. An acknowledgement within 2 business days, from a person.
2. An assessment, and a severity, within 5 business days.
3. A fix released as a new version, and this file's advisory list updated.
4. Credit in the release notes under the name you choose, or none if you prefer.

Please give us time to release a fix before describing the problem publicly. We
do not pay for reports and we will not threaten anyone who sends one in good
faith.

## What is in scope

The code in this repository: the two clients and the domain modules they are
built from. Concretely, and these are the things worth looking at:

- **The retry policy.** A client that retried a write that may have taken
  effect would issue a record twice. Every `POST` carries one idempotency key
  across all of its attempts, a `POST` answered `500` is never retried, and a
  redirect is never followed with the key on it.
- **Offline proof verification.** `verifyProofOffline` and
  `verify_proof_offline` recompute a Merkle root from a leaf and a path. A
  proof that verifies when it should not is the most serious bug either package
  can have.
- **What the client carries where.** The API key goes in one header, to one
  origin. A cross-origin redirect must drop it; a client that leaks it to a
  host that answered a redirect is a vulnerability, not a bug.
- **What the client prints.** No key, no payload and nothing about a person may
  appear in a string representation, a log line or an error message.

## What is not in scope

- The TraceTus API, the console and the public verifier. They are not in this
  repository. A problem in one of them goes to the same address and is handled
  under the platform's own policy.
- A dependency's own vulnerability, unless this repository pins or reaches the
  vulnerable path. Report it upstream; tell us too, so the floor moves.
- A denial of service against your own machine from input you chose yourself.
- Anything that needs an attacker to already hold a valid API key of the
  account being attacked.

## How these packages are published

Both are published by this repository's `release.yml`, on a tag, through the
registries' **trusted publishing**: npm and PyPI verify the workflow by a
short-lived identity token that GitHub mints for that run. **No publishing
token is stored anywhere**, in this repository or outside it. The npm package
carries a provenance attestation that names the commit and the run it was
built from, and `npm audit signatures` checks it.

Building and publishing are separate jobs, and only the publishing ones can
mint that token. Nothing else runs in them: no install that resolves, no
global `npm install`, no browser download, no test suite. The jobs that do all
of that have no token to steal, and hand over exactly the tarball and the
distributions that get published.

**One exception, and it is the first version of `@tracetus/sdk`.** Trusted
publishing cannot create a package that does not exist on the registry, so
`0.1.0` was published by hand, from a machine, and carries **no provenance
attestation**. Every version after it comes from the workflow and carries one.
If you are checking signatures and find that version without an attestation,
that is why.

The source of truth is TraceTus's private monorepo. This repository is rebuilt
from one commit of it at each release, from an explicit list of paths, by a
command that refuses to produce a tree that holds a secret, a file outside
that list, a symlink, bytes that are not what a file's name says, or anything
private to that repository. Two separate extractions of the commit have to
give the same tree, and the release commit records the git tree id, so the
tree that was reviewed is the tree that was pushed.

## Supported versions

The current minor of each package. A fix goes out as a new patch; versions are
not back-ported, and nothing is unpublished — a version that vanished would
break whoever already installed it. A version that is dangerous rather than
merely wrong is deprecated on the registry, with the replacement named.

## Advisories

None.
