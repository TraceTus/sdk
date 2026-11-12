from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.record_detail_env_label import RecordDetailEnvLabel

if TYPE_CHECKING:
    from ..models.record_detail_anchors_item import RecordDetailAnchorsItem
    from ..models.record_detail_batch_type_0 import RecordDetailBatchType0
    from ..models.record_detail_proof_type_0 import RecordDetailProofType0
    from ..models.record_detail_record import RecordDetailRecord


T = TypeVar("T", bound="RecordDetail")


@_attrs_define
class RecordDetail:
    """
    Attributes:
        env_label (RecordDetailEnvLabel):  Example: simulation.
        record (RecordDetailRecord):
        batch (None | RecordDetailBatchType0):
        proof (None | RecordDetailProofType0):
        anchors (list[RecordDetailAnchorsItem]):
    """

    env_label: RecordDetailEnvLabel
    record: RecordDetailRecord
    batch: None | RecordDetailBatchType0
    proof: None | RecordDetailProofType0
    anchors: list[RecordDetailAnchorsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.record_detail_batch_type_0 import RecordDetailBatchType0
        from ..models.record_detail_proof_type_0 import RecordDetailProofType0

        env_label = self.env_label.value

        record = self.record.to_dict()

        batch: dict[str, Any] | None
        if isinstance(self.batch, RecordDetailBatchType0):
            batch = self.batch.to_dict()
        else:
            batch = self.batch

        proof: dict[str, Any] | None
        if isinstance(self.proof, RecordDetailProofType0):
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
                "record": record,
                "batch": batch,
                "proof": proof,
                "anchors": anchors,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.record_detail_anchors_item import RecordDetailAnchorsItem
        from ..models.record_detail_batch_type_0 import RecordDetailBatchType0
        from ..models.record_detail_proof_type_0 import RecordDetailProofType0
        from ..models.record_detail_record import RecordDetailRecord

        d = dict(src_dict)
        env_label = RecordDetailEnvLabel(d.pop("envLabel"))

        record = RecordDetailRecord.from_dict(d.pop("record"))

        def _parse_batch(data: object) -> None | RecordDetailBatchType0:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                batch_type_0 = RecordDetailBatchType0.from_dict(data)

                return batch_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RecordDetailBatchType0, data)

        batch = _parse_batch(d.pop("batch"))

        def _parse_proof(data: object) -> None | RecordDetailProofType0:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                proof_type_0 = RecordDetailProofType0.from_dict(data)

                return proof_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RecordDetailProofType0, data)

        proof = _parse_proof(d.pop("proof"))

        anchors = []
        _anchors = d.pop("anchors")
        for anchors_item_data in _anchors:
            anchors_item = RecordDetailAnchorsItem.from_dict(anchors_item_data)

            anchors.append(anchors_item)

        record_detail = cls(
            env_label=env_label,
            record=record,
            batch=batch,
            proof=proof,
            anchors=anchors,
        )

        record_detail.additional_properties = d
        return record_detail

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
