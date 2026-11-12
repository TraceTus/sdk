from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

if TYPE_CHECKING:
    from ..models.error_response_error_issues_item import ErrorResponseErrorIssuesItem


T = TypeVar("T", bound="ErrorResponseError")


@_attrs_define
class ErrorResponseError:
    """
    Attributes:
        code (str):  Example: SCHEMA_UNKNOWN.
        message (str):
        issues (list[ErrorResponseErrorIssuesItem]):
    """

    code: str
    message: str
    issues: list[ErrorResponseErrorIssuesItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        message = self.message

        issues = []
        for issues_item_data in self.issues:
            issues_item = issues_item_data.to_dict()
            issues.append(issues_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "message": message,
                "issues": issues,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.error_response_error_issues_item import ErrorResponseErrorIssuesItem

        d = dict(src_dict)
        code = d.pop("code")

        message = d.pop("message")

        issues = []
        _issues = d.pop("issues")
        for issues_item_data in _issues:
            issues_item = ErrorResponseErrorIssuesItem.from_dict(issues_item_data)

            issues.append(issues_item)

        error_response_error = cls(
            code=code,
            message=message,
            issues=issues,
        )

        error_response_error.additional_properties = d
        return error_response_error

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
