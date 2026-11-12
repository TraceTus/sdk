from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

if TYPE_CHECKING:
    from ..models.add_connector_device_request_mapping import AddConnectorDeviceRequestMapping


T = TypeVar("T", bound="AddConnectorDeviceRequest")


@_attrs_define
class AddConnectorDeviceRequest:
    """
    Attributes:
        network_device_id (str): Address of the device on its own network. It is stored and never returned, never logged
            and never part of a record. Example: example-tracker-01.
        mapping (AddConnectorDeviceRequestMapping): What this kind of connector needs to turn what the device delivers
            into record content. Its shape belongs to the kind; the platform stores it and does not read it. A field whose
            name looks like a position is refused. Example: {'deviceRef': 'dev_0000000000', 'placeCode': 'XX-0000',
            'metrics': {'temperatureC': {'metric': 'TEMPERATURE', 'unit': 'C'}}}.
    """

    network_device_id: str
    mapping: AddConnectorDeviceRequestMapping
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        network_device_id = self.network_device_id

        mapping = self.mapping.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "networkDeviceId": network_device_id,
                "mapping": mapping,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.add_connector_device_request_mapping import AddConnectorDeviceRequestMapping

        d = dict(src_dict)
        network_device_id = d.pop("networkDeviceId")

        mapping = AddConnectorDeviceRequestMapping.from_dict(d.pop("mapping"))

        add_connector_device_request = cls(
            network_device_id=network_device_id,
            mapping=mapping,
        )

        add_connector_device_request.additional_properties = d
        return add_connector_device_request

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
