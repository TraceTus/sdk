from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse
from typing_extensions import Self

from ..models.verify_response_record_status import VerifyResponseRecordStatus

T = TypeVar("T", bound="VerifyResponseRecord")


@_attrs_define
class VerifyResponseRecord:
    """
    Attributes:
        id (str):
        schema_id (str):  Example: tracetus:custody-event:1.
        record_hash (str):
        status (VerifyResponseRecordStatus):
        created_at (datetime.datetime):
    """

    id: str
    schema_id: str
    record_hash: str
    status: VerifyResponseRecordStatus
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        schema_id = self.schema_id

        record_hash = self.record_hash

        status = self.status.value

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "schemaId": schema_id,
                "recordHash": record_hash,
                "status": status,
                "createdAt": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        id = d.pop("id")

        schema_id = d.pop("schemaId")

        record_hash = d.pop("recordHash")

        status = VerifyResponseRecordStatus(d.pop("status"))

        created_at = isoparse(d.pop("createdAt"))

        verify_response_record = cls(
            id=id,
            schema_id=schema_id,
            record_hash=record_hash,
            status=status,
            created_at=created_at,
        )

        verify_response_record.additional_properties = d
        return verify_response_record

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
