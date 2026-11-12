"""Offline verification of an inclusion proof.

The same Merkle rule as ``@tracetus/core``: leaves and nodes are 32-byte
keccak256 digests, a pair is sorted bytewise before it is hashed, and an odd
node climbs alone. Whoever holds a record hash, its siblings and the batch
root can check them here without asking the API for anything.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from Crypto.Hash import keccak

HEX32 = re.compile(r"^0x[0-9a-f]{64}$")


def is_hex32(value: Any) -> bool:
    return isinstance(value, str) and HEX32.fullmatch(value) is not None


def _keccak(data: bytes) -> bytes:
    digest = keccak.new(digest_bits=256)
    digest.update(data)
    return digest.digest()


def hash_pair(left: str, right: str) -> str:
    """keccak256 of the two nodes, smaller first, as the tree builds them."""
    a, b = bytes.fromhex(left[2:]), bytes.fromhex(right[2:])
    pair = a + b if a <= b else b + a
    return "0x" + _keccak(pair).hex()


def verify_proof_offline(record_hash: str, siblings: Sequence[str], root: str) -> bool:
    """True when the siblings climb from the record hash to the root.

    Malformed hex anywhere is False, never an exception.
    """
    if not is_hex32(record_hash) or not is_hex32(root):
        return False
    if any(not is_hex32(node) for node in siblings):
        return False

    accumulator = record_hash
    for node in siblings:
        accumulator = hash_pair(accumulator, node)

    return accumulator == root


def verify_response_offline(response: Mapping[str, Any]) -> bool | None:
    """The same check over a ``GET /v1/verify/{id}`` or ``GET /v1/records/{id}`` body.

    Accepts the parsed JSON (a mapping) or a generated model through its
    ``to_dict()``. ``None`` while the record has no proof or its batch has no
    root yet; the proof must name the batch root it claims to reach.
    """
    body = response.to_dict() if hasattr(response, "to_dict") else response
    proof = body.get("proof")
    batch = body.get("batch")
    root = batch.get("merkleRoot") if isinstance(batch, Mapping) else None

    if not isinstance(proof, Mapping) or root is None:
        return None

    record = body.get("record")
    record_hash = record.get("recordHash") if isinstance(record, Mapping) else None

    if proof.get("root") != root or not isinstance(record_hash, str):
        return False

    siblings = proof.get("siblings")
    if not isinstance(siblings, list):
        return False

    return verify_proof_offline(record_hash, siblings, root)
