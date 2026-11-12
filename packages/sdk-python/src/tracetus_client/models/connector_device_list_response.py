from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.connector_device_list_response_env_label import ConnectorDeviceListResponseEnvLabel

if TYPE_CHECKING:
    from ..models.connector_device_list_response_devices_item import (
        ConnectorDeviceListResponseDevicesItem,
    )


T = TypeVar("T", bound="ConnectorDeviceListResponse")


@_attrs_define
class ConnectorDeviceListResponse:
    """
    Attributes:
        env_label (ConnectorDeviceListResponseEnvLabel):  Example: simulation.
        count (int):
        next_cursor (None | str): Pass it as `cursor` to read the next page. Null when this page is the last.
        devices (list[ConnectorDeviceListResponseDevicesItem]):
    """

    env_label: ConnectorDeviceListResponseEnvLabel
    count: int
    next_cursor: None | str
    devices: list[ConnectorDeviceListResponseDevicesItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        count = self.count

        next_cursor: None | str
        next_cursor = self.next_cursor

        devices = []
        for devices_item_data in self.devices:
            devices_item = devices_item_data.to_dict()
            devices.append(devices_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "count": count,
                "nextCursor": next_cursor,
                "devices": devices,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.connector_device_list_response_devices_item import (
            ConnectorDeviceListResponseDevicesItem,
        )

        d = dict(src_dict)
        env_label = ConnectorDeviceListResponseEnvLabel(d.pop("envLabel"))

        count = d.pop("count")

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        devices = []
        _devices = d.pop("devices")
        for devices_item_data in _devices:
            devices_item = ConnectorDeviceListResponseDevicesItem.from_dict(devices_item_data)

            devices.append(devices_item)

        connector_device_list_response = cls(
            env_label=env_label,
            count=count,
            next_cursor=next_cursor,
            devices=devices,
        )

        connector_device_list_response.additional_properties = d
        return connector_device_list_response

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
