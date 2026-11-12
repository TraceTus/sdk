from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse
from typing_extensions import Self

from ..models.record_detail_record_status import RecordDetailRecordStatus

T = TypeVar("T", bound="RecordDetailRecord")


@_attrs_define
class RecordDetailRecord:
    """
    Attributes:
        id (str):
        schema_id (str):  Example: tracetus:custody-event:1.
        record_hash (str):
        salt (str): Salt of the hash, handed to the issuer. Without it the content cannot be proven.
        status (RecordDetailRecordStatus):
        created_at (datetime.datetime):
        ref_record_id (None | str):
    """

    id: str
    schema_id: str
    record_hash: str
    salt: str
    status: RecordDetailRecordStatus
    created_at: datetime.datetime
    ref_record_id: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        schema_id = self.schema_id

        record_hash = self.record_hash

        salt = self.salt

        status = self.status.value

        created_at = self.created_at.isoformat()

        ref_record_id: None | str
        ref_record_id = self.ref_record_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "schemaId": schema_id,
                "recordHash": record_hash,
                "salt": salt,
                "status": status,
                "createdAt": created_at,
                "refRecordId": ref_record_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        id = d.pop("id")

        schema_id = d.pop("schemaId")

        record_hash = d.pop("recordHash")

        salt = d.pop("salt")

        status = RecordDetailRecordStatus(d.pop("status"))

        created_at = isoparse(d.pop("createdAt"))

        def _parse_ref_record_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        ref_record_id = _parse_ref_record_id(d.pop("refRecordId"))

        record_detail_record = cls(
            id=id,
            schema_id=schema_id,
            record_hash=record_hash,
            salt=salt,
            status=status,
            created_at=created_at,
            ref_record_id=ref_record_id,
        )

        record_detail_record.additional_properties = d
        return record_detail_record

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
