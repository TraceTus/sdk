# TraceTus clients

The JavaScript and Python clients of the TraceTus API, and the source they are
built from. TraceTus is a proof layer for origin, certification and custody
records: a record is issued, a batch of records is anchored on a blockchain as
one Merkle root, and anyone can check that a record is in that batch without
asking us.

| Package | Registry |
|---|---|
| `@tracetus/sdk` | npm |
| `tracetus` | PyPI |

**The source arrives here with the first release.** This repository is a mirror:
at each release it is rebuilt from the platform's own repository and published
here, so the clients are not a binary. Until the first release lands, the API
and both clients are documented at [docs.tracetus.com](https://docs.tracetus.com).

## Reporting a problem

Open an issue in this repository. Please do not paste an API key, a payload or
anything about a person.

## Reporting a vulnerability

Write to security@tracetus.com rather than opening an issue.

## Licence

Apache-2.0. See `LICENSE`.
