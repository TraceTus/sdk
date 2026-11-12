from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse
from typing_extensions import Self

if TYPE_CHECKING:
    from ..models.connector_device_response_device_mapping import (
        ConnectorDeviceResponseDeviceMapping,
    )


T = TypeVar("T", bound="ConnectorDeviceResponseDevice")


@_attrs_define
class ConnectorDeviceResponseDevice:
    """
    Attributes:
        id (str):
        mapping (ConnectorDeviceResponseDeviceMapping): What this kind of connector needs to turn what the device
            delivers into record content. Its shape belongs to the kind; the platform stores it and does not read it. A
            field whose name looks like a position is refused. Example: {'deviceRef': 'dev_0000000000', 'placeCode':
            'XX-0000', 'metrics': {'temperatureC': {'metric': 'TEMPERATURE', 'unit': 'C'}}}.
        created_at (datetime.datetime):
    """

    id: str
    mapping: ConnectorDeviceResponseDeviceMapping
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        mapping = self.mapping.to_dict()

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "mapping": mapping,
                "createdAt": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.connector_device_response_device_mapping import (
            ConnectorDeviceResponseDeviceMapping,
        )

        d = dict(src_dict)
        id = d.pop("id")

        mapping = ConnectorDeviceResponseDeviceMapping.from_dict(d.pop("mapping"))

        created_at = isoparse(d.pop("createdAt"))

        connector_device_response_device = cls(
            id=id,
            mapping=mapping,
            created_at=created_at,
        )

        connector_device_response_device.additional_properties = d
        return connector_device_response_device

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
