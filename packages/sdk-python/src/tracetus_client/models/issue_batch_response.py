from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.issue_batch_response_env_label import IssueBatchResponseEnvLabel

if TYPE_CHECKING:
    from ..models.issue_batch_response_records_item import IssueBatchResponseRecordsItem


T = TypeVar("T", bound="IssueBatchResponse")


@_attrs_define
class IssueBatchResponse:
    """
    Attributes:
        env_label (IssueBatchResponseEnvLabel):  Example: simulation.
        count (int):
        records (list[IssueBatchResponseRecordsItem]):
    """

    env_label: IssueBatchResponseEnvLabel
    count: int
    records: list[IssueBatchResponseRecordsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        count = self.count

        records = []
        for records_item_data in self.records:
            records_item = records_item_data.to_dict()
            records.append(records_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "count": count,
                "records": records,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.issue_batch_response_records_item import IssueBatchResponseRecordsItem

        d = dict(src_dict)
        env_label = IssueBatchResponseEnvLabel(d.pop("envLabel"))

        count = d.pop("count")

        records = []
        _records = d.pop("records")
        for records_item_data in _records:
            records_item = IssueBatchResponseRecordsItem.from_dict(records_item_data)

            records.append(records_item)

        issue_batch_response = cls(
            env_label=env_label,
            count=count,
            records=records,
        )

        issue_batch_response.additional_properties = d
        return issue_batch_response

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
