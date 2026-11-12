from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.connector_device_response_env_label import ConnectorDeviceResponseEnvLabel

if TYPE_CHECKING:
    from ..models.connector_device_response_device import ConnectorDeviceResponseDevice


T = TypeVar("T", bound="ConnectorDeviceResponse")


@_attrs_define
class ConnectorDeviceResponse:
    """
    Attributes:
        env_label (ConnectorDeviceResponseEnvLabel):  Example: simulation.
        device (ConnectorDeviceResponseDevice):
    """

    env_label: ConnectorDeviceResponseEnvLabel
    device: ConnectorDeviceResponseDevice
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        device = self.device.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "device": device,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.connector_device_response_device import ConnectorDeviceResponseDevice

        d = dict(src_dict)
        env_label = ConnectorDeviceResponseEnvLabel(d.pop("envLabel"))

        device = ConnectorDeviceResponseDevice.from_dict(d.pop("device"))

        connector_device_response = cls(
            env_label=env_label,
            device=device,
        )

        connector_device_response.additional_properties = d
        return connector_device_response

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
