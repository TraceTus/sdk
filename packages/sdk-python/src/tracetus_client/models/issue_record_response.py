from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.issue_record_response_env_label import IssueRecordResponseEnvLabel

if TYPE_CHECKING:
    from ..models.issue_record_response_record import IssueRecordResponseRecord


T = TypeVar("T", bound="IssueRecordResponse")


@_attrs_define
class IssueRecordResponse:
    """
    Attributes:
        env_label (IssueRecordResponseEnvLabel):  Example: simulation.
        record (IssueRecordResponseRecord):
    """

    env_label: IssueRecordResponseEnvLabel
    record: IssueRecordResponseRecord
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        record = self.record.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "record": record,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.issue_record_response_record import IssueRecordResponseRecord

        d = dict(src_dict)
        env_label = IssueRecordResponseEnvLabel(d.pop("envLabel"))

        record = IssueRecordResponseRecord.from_dict(d.pop("record"))

        issue_record_response = cls(
            env_label=env_label,
            record=record,
        )

        issue_record_response.additional_properties = d
        return issue_record_response

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
