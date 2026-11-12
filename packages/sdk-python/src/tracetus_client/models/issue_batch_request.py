from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

if TYPE_CHECKING:
    from ..models.issue_batch_request_records_item import IssueBatchRequestRecordsItem


T = TypeVar("T", bound="IssueBatchRequest")


@_attrs_define
class IssueBatchRequest:
    """
    Attributes:
        schema_id (str):  Example: tracetus:custody-event:1.
        records (list[IssueBatchRequestRecordsItem]):
    """

    schema_id: str
    records: list[IssueBatchRequestRecordsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        schema_id = self.schema_id

        records = []
        for records_item_data in self.records:
            records_item = records_item_data.to_dict()
            records.append(records_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "schemaId": schema_id,
                "records": records,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.issue_batch_request_records_item import IssueBatchRequestRecordsItem

        d = dict(src_dict)
        schema_id = d.pop("schemaId")

        records = []
        _records = d.pop("records")
        for records_item_data in _records:
            records_item = IssueBatchRequestRecordsItem.from_dict(records_item_data)

            records.append(records_item)

        issue_batch_request = cls(
            schema_id=schema_id,
            records=records,
        )

        issue_batch_request.additional_properties = d
        return issue_batch_request

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
