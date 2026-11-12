# TraceTus clients

The JavaScript and Python clients of the TraceTus API, and the source they are
built from. TraceTus is a proof layer for origin, certification and custody
records: a record is issued, a batch of records is anchored on a blockchain as
one Merkle root, and anyone can check that a record is in that batch without
asking us.

```bash
npm install @tracetus/sdk
pip install tracetus
```

| Package | Registry | Directory |
|---|---|---|
| `@tracetus/sdk` | [npm](https://www.npmjs.com/package/@tracetus/sdk) | `packages/sdk-js` |
| `tracetus` | [PyPI](https://pypi.org/project/tracetus/) | `packages/sdk-python` |

Each directory has its own README with the whole surface. The API itself is
documented at [docs.tracetus.com](https://docs.tracetus.com).

## Why this repository exists, and what it is not

**This is a mirror, published so the clients are not a binary.** The source of
truth is TraceTus's own monorepo, which is private: the API, the contracts, the
console and the verifier live there with these two packages, and that is where
they are changed. At each release the mirror is rebuilt from a single commit of
it, from an explicit list of paths, and arrives here as one commit — through a
pull request from a `release/<version>` branch, so that this repository's own
suites run on it before it reaches `main`.

So: **nobody develops here.** Every file is replaced wholesale by the next
release, so a commit of your own does not survive one.

**A pull request you open cannot be merged as it stands** — only a release
branch is ever merged. What happens to yours instead is that it is read,
carried into the monorepo with you credited in the change, and comes back out
in the following release. If you are about to write a patch, open an issue
first and say what you intend: that is the cheapest way for both of us.

What is here is everything the two packages are built from and tested with:

- `apps/api/openapi.json` — the API contract. Both clients' request layers are
  generated from it, and neither generated half is edited by hand.
- `packages/core` — the hexadecimal and Merkle modules. Offline proof
  verification uses the same code that builds the proof, which is the point of
  it; the rest of that package is the platform's and stays in the monorepo.
- `packages/sdk-js`, `packages/sdk-python` — the two clients, with their suites
  and their examples.

## Reporting a problem

Open an issue in this repository. What helps:

- the package and the version (`npm ls @tracetus/sdk`, `pip show tracetus`);
- the runtime and its version (Node, a browser, an edge runtime, CPython);
- what you called and what came back — the `code` of the error and the request
  id are in the answer, and both are safe to paste;
- what you expected instead.

**Please do not paste an API key, a payload or anything about a person.** An
error from this client carries a code and a request id on purpose, so that a
report needs neither.

Issues about the API itself — a route, a schema, a verification result — are
also welcome here; they are carried where they belong.

## Reporting a vulnerability

**Do not open an issue.** Write to **security@tracetus.com**, which is
answered within 2 business days. `SECURITY.md` says what to expect, what is in
scope and what is not.

## Building it yourself

Node 22 or newer and pnpm for the JavaScript client, Python 3.10 or newer for
the Python one.

```bash
pnpm install --frozen-lockfile
pnpm build            # the domain modules, then the client, in ESM and CommonJS
pnpm test             # both JavaScript suites, including one in a real browser
pnpm typecheck
```

The browser suite needs one download, once:
`pnpm --filter @tracetus/sdk exec playwright install chromium-headless-shell`.

```bash
cd packages/sdk-python
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

`pnpm-lock.yaml` is resolved for this workspace and reviewed in the monorepo
before it is copied here, like everything else: the install in the pipeline
and the install on your machine are the same install, and every version in it
is one the monorepo already resolved and tested. So this whole repository is
byte for byte what one commit of that one holds, which is why the release that
produced it can be checked by rebuilding it — the tree id in the release
commit is the check.

Nothing committed on top of a release survives the next one — a fix, a
lockfile, a tweak. That is what "mirror" means here.

The published JavaScript package has no runtime dependency at all, and the
Python one declares floors rather than pins, so what an install resolves here
is a development toolchain and never what a user of the packages gets.

## Licence

Apache-2.0. See `LICENSE`.
