from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.removed_connector_device_response_env_label import (
    RemovedConnectorDeviceResponseEnvLabel,
)

T = TypeVar("T", bound="RemovedConnectorDeviceResponse")


@_attrs_define
class RemovedConnectorDeviceResponse:
    """
    Attributes:
        env_label (RemovedConnectorDeviceResponseEnvLabel):  Example: simulation.
        device_id (str):
        removed (bool):
    """

    env_label: RemovedConnectorDeviceResponseEnvLabel
    device_id: str
    removed: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        device_id = self.device_id

        removed = self.removed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "deviceId": device_id,
                "removed": removed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        env_label = RemovedConnectorDeviceResponseEnvLabel(d.pop("envLabel"))

        device_id = d.pop("deviceId")

        removed = d.pop("removed")

        removed_connector_device_response = cls(
            env_label=env_label,
            device_id=device_id,
            removed=removed,
        )

        removed_connector_device_response.additional_properties = d
        return removed_connector_device_response

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
