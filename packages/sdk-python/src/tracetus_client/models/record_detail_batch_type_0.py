from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse
from typing_extensions import Self

from ..models.record_detail_batch_type_0_status import RecordDetailBatchType0Status

T = TypeVar("T", bound="RecordDetailBatchType0")


@_attrs_define
class RecordDetailBatchType0:
    """
    Attributes:
        id (str):
        merkle_root (None | str):
        leaf_count (int):
        status (RecordDetailBatchType0Status):
        sealed_at (datetime.datetime | None):
    """

    id: str
    merkle_root: None | str
    leaf_count: int
    status: RecordDetailBatchType0Status
    sealed_at: datetime.datetime | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        merkle_root: None | str
        merkle_root = self.merkle_root

        leaf_count = self.leaf_count

        status = self.status.value

        sealed_at: None | str
        if isinstance(self.sealed_at, datetime.datetime):
            sealed_at = self.sealed_at.isoformat()
        else:
            sealed_at = self.sealed_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "merkleRoot": merkle_root,
                "leafCount": leaf_count,
                "status": status,
                "sealedAt": sealed_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        id = d.pop("id")

        def _parse_merkle_root(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        merkle_root = _parse_merkle_root(d.pop("merkleRoot"))

        leaf_count = d.pop("leafCount")

        status = RecordDetailBatchType0Status(d.pop("status"))

        def _parse_sealed_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                sealed_at_type_0 = isoparse(data)

                return sealed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        sealed_at = _parse_sealed_at(d.pop("sealedAt"))

        record_detail_batch_type_0 = cls(
            id=id,
            merkle_root=merkle_root,
            leaf_count=leaf_count,
            status=status,
            sealed_at=sealed_at,
        )

        record_detail_batch_type_0.additional_properties = d
        return record_detail_batch_type_0

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
