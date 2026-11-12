"""Vectors produced by ``@tracetus/core`` (buildTree, getProof, hashRecord) for
three leaves; the Python check must agree with the JavaScript one byte for byte."""

import pytest

from tracetus import verify_proof_offline, verify_response_offline
from tracetus.proof import hash_pair

LEAVES = [
    "0x2c5ed3278914148650b990f0d992dd8e7f8d9728a56a555226031b1f93778cfb",
    "0x360f13bff18998c6e745e8a32f626fa646e95d2d4dcd1c0b404a45cc62575af1",
    "0xa659d0739ad4c507e734ca9e168983854e0634e46328dd8acd460e7fa24c6f51",
]
ROOT = "0xcd24ea7103a04a41d8ddbf00cb9ed4011e6e9b0045f528478367d947fbc3a2a4"
PROOFS = [
    [LEAVES[1], LEAVES[2]],
    [LEAVES[0], LEAVES[2]],
    ["0x971aeab0d34428cfb7afd4f1dc2c7f8926e2ed3b9663c9d762d59a703b232834"],
]
OTHER = "0x" + "ee" * 32


def response(**overrides):
    body = {
        "record": {"id": "rec_" + "0" * 32, "recordHash": LEAVES[1], "status": "anchored"},
        "proof": {"leafIndex": 1, "siblings": PROOFS[1], "root": ROOT},
        "batch": {"id": "bat_" + "0" * 32, "merkleRoot": ROOT, "leafCount": 3},
    }
    body.update(overrides)
    return body


@pytest.mark.parametrize("index", [0, 1, 2])
def test_accepts_every_proof_the_tree_produced(index):
    assert verify_proof_offline(LEAVES[index], PROOFS[index], ROOT) is True


def test_sorts_the_pair_before_hashing():
    assert hash_pair(LEAVES[0], LEAVES[1]) == hash_pair(LEAVES[1], LEAVES[0])
    assert hash_pair(LEAVES[0], LEAVES[1]) == PROOFS[2][0]


def test_refuses_a_changed_leaf_root_or_sibling():
    assert verify_proof_offline(OTHER, PROOFS[1], ROOT) is False
    assert verify_proof_offline(LEAVES[1], PROOFS[1], OTHER) is False
    assert verify_proof_offline(LEAVES[1], [OTHER], ROOT) is False


def test_returns_false_instead_of_raising_for_malformed_hex():
    assert verify_proof_offline("not-hex", PROOFS[1], ROOT) is False
    assert verify_proof_offline(LEAVES[1], ["0xzz"], ROOT) is False
    assert verify_proof_offline(LEAVES[1], PROOFS[1], "0x") is False
    assert verify_proof_offline(LEAVES[1], [42], ROOT) is False  # type: ignore[list-item]


def test_checks_a_verification_body_against_its_batch_root():
    assert verify_response_offline(response()) is True


def test_is_none_while_there_is_no_proof_or_no_root_yet():
    assert verify_response_offline(response(proof=None)) is None
    assert verify_response_offline(response(batch=None)) is None
    assert verify_response_offline(response(batch={"id": "bat_x", "merkleRoot": None})) is None


def test_refuses_a_proof_naming_another_root_or_a_tampered_record():
    assert verify_response_offline(response(proof={"siblings": PROOFS[1], "root": OTHER})) is False
    tampered = response()
    tampered["record"]["recordHash"] = OTHER
    assert verify_response_offline(tampered) is False
    assert verify_response_offline(response(proof={"root": ROOT, "siblings": "x"})) is False


def test_accepts_a_generated_model_through_to_dict():
    class Model:
        def to_dict(self):
            return response()

    assert verify_response_offline(Model()) is True  # type: ignore[arg-type]
