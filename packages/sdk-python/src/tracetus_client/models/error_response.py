from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.error_response_env_label import ErrorResponseEnvLabel

if TYPE_CHECKING:
    from ..models.error_response_error import ErrorResponseError


T = TypeVar("T", bound="ErrorResponse")


@_attrs_define
class ErrorResponse:
    """
    Attributes:
        env_label (ErrorResponseEnvLabel):  Example: simulation.
        error (ErrorResponseError):
    """

    env_label: ErrorResponseEnvLabel
    error: ErrorResponseError
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        error = self.error.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "error": error,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.error_response_error import ErrorResponseError

        d = dict(src_dict)
        env_label = ErrorResponseEnvLabel(d.pop("envLabel"))

        error = ErrorResponseError.from_dict(d.pop("error"))

        error_response = cls(
            env_label=env_label,
            error=error,
        )

        error_response.additional_properties = d
        return error_response

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
