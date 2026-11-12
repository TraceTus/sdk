from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.verify_response_env_label import VerifyResponseEnvLabel

if TYPE_CHECKING:
    from ..models.verify_response_anchors_item import VerifyResponseAnchorsItem
    from ..models.verify_response_batch_type_0 import VerifyResponseBatchType0
    from ..models.verify_response_issuer import VerifyResponseIssuer
    from ..models.verify_response_proof_type_0 import VerifyResponseProofType0
    from ..models.verify_response_record import VerifyResponseRecord


T = TypeVar("T", bound="VerifyResponse")


@_attrs_define
class VerifyResponse:
    """
    Attributes:
        env_label (VerifyResponseEnvLabel):  Example: simulation.
        proof_valid (bool | None): Proof checked against the batch root, recomputed here. The check that counts is the
            public verifier's, against the network.
        record (VerifyResponseRecord):
        issuer (VerifyResponseIssuer): Issuer, a legal entity. A natural person never appears in the verifier.
        batch (None | VerifyResponseBatchType0):
        proof (None | VerifyResponseProofType0):
        anchors (list[VerifyResponseAnchorsItem]):
    """

    env_label: VerifyResponseEnvLabel
    proof_valid: bool | None
    record: VerifyResponseRecord
    issuer: VerifyResponseIssuer
    batch: None | VerifyResponseBatchType0
    proof: None | VerifyResponseProofType0
    anchors: list[VerifyResponseAnchorsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.verify_response_batch_type_0 import VerifyResponseBatchType0
        from ..models.verify_response_proof_type_0 import VerifyResponseProofType0

        env_label = self.env_label.value

        proof_valid: bool | None
        proof_valid = self.proof_valid

        record = self.record.to_dict()

        issuer = self.issuer.to_dict()

        batch: dict[str, Any] | None
        if isinstance(self.batch, VerifyResponseBatchType0):
            batch = self.batch.to_dict()
        else:
            batch = self.batch

        proof: dict[str, Any] | None
        if isinstance(self.proof, VerifyResponseProofType0):
            proof = self.proof.to_dict()
        else:
            proof = self.proof

        anchors = []
        for anchors_item_data in self.anchors:
            anchors_item = anchors_item_data.to_dict()
            anchors.append(anchors_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "proofValid": proof_valid,
                "record": record,
                "issuer": issuer,
                "batch": batch,
                "proof": proof,
                "anchors": anchors,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.verify_response_anchors_item import VerifyResponseAnchorsItem
        from ..models.verify_response_batch_type_0 import VerifyResponseBatchType0
        from ..models.verify_response_issuer import VerifyResponseIssuer
        from ..models.verify_response_proof_type_0 import VerifyResponseProofType0
        from ..models.verify_response_record import VerifyResponseRecord

        d = dict(src_dict)
        env_label = VerifyResponseEnvLabel(d.pop("envLabel"))

        def _parse_proof_valid(data: object) -> bool | None:
            if data is None:
                return data
            return cast(bool | None, data)

        proof_valid = _parse_proof_valid(d.pop("proofValid"))

        record = VerifyResponseRecord.from_dict(d.pop("record"))

        issuer = VerifyResponseIssuer.from_dict(d.pop("issuer"))

        def _parse_batch(data: object) -> None | VerifyResponseBatchType0:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                batch_type_0 = VerifyResponseBatchType0.from_dict(data)

                return batch_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | VerifyResponseBatchType0, data)

        batch = _parse_batch(d.pop("batch"))

        def _parse_proof(data: object) -> None | VerifyResponseProofType0:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                proof_type_0 = VerifyResponseProofType0.from_dict(data)

                return proof_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | VerifyResponseProofType0, data)

        proof = _parse_proof(d.pop("proof"))

        anchors = []
        _anchors = d.pop("anchors")
        for anchors_item_data in _anchors:
            anchors_item = VerifyResponseAnchorsItem.from_dict(anchors_item_data)

            anchors.append(anchors_item)

        verify_response = cls(
            env_label=env_label,
            proof_valid=proof_valid,
            record=record,
            issuer=issuer,
            batch=batch,
            proof=proof,
            anchors=anchors,
        )

        verify_response.additional_properties = d
        return verify_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
