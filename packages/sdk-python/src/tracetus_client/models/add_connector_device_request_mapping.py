from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

T = TypeVar("T", bound="AddConnectorDeviceRequestMapping")


@_attrs_define
class AddConnectorDeviceRequestMapping:
    """What this kind of connector needs to turn what the device delivers into record content. Its shape belongs to the
    kind; the platform stores it and does not read it. A field whose name looks like a position is refused.

        Example:
            {'deviceRef': 'dev_0000000000', 'placeCode': 'XX-0000', 'metrics': {'temperatureC': {'metric': 'TEMPERATURE',
                'unit': 'C'}}}

    """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        add_connector_device_request_mapping = cls()

        add_connector_device_request_mapping.additional_properties = d
        return add_connector_device_request_mapping

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
