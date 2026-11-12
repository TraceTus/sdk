from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse
from typing_extensions import Self

from ..models.connector_response_connector_kind import ConnectorResponseConnectorKind
from ..models.connector_response_connector_status import ConnectorResponseConnectorStatus

T = TypeVar("T", bound="ConnectorResponseConnector")


@_attrs_define
class ConnectorResponseConnector:
    """
    Attributes:
        id (str):
        kind (ConnectorResponseConnectorKind): Kind of connector. The URL a network calls is derived from it. Example:
            ttn.
        name (str): Operational name of the connector, for whoever runs it. No personal data. Example: field oracle.
        status (ConnectorResponseConnectorStatus):
        created_at (datetime.datetime):
        disabled_at (datetime.datetime | None):
        uplink_path (str): Path the network calls, on the connector deployment that serves this kind. The base URL is
            the deployment's, not the API's. Example: /ttn/con_0123456789abcdef0123456789abcdef/uplink.
    """

    id: str
    kind: ConnectorResponseConnectorKind
    name: str
    status: ConnectorResponseConnectorStatus
    created_at: datetime.datetime
    disabled_at: datetime.datetime | None
    uplink_path: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        kind = self.kind.value

        name = self.name

        status = self.status.value

        created_at = self.created_at.isoformat()

        disabled_at: None | str
        if isinstance(self.disabled_at, datetime.datetime):
            disabled_at = self.disabled_at.isoformat()
        else:
            disabled_at = self.disabled_at

        uplink_path = self.uplink_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "kind": kind,
                "name": name,
                "status": status,
                "createdAt": created_at,
                "disabledAt": disabled_at,
                "uplinkPath": uplink_path,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        id = d.pop("id")

        kind = ConnectorResponseConnectorKind(d.pop("kind"))

        name = d.pop("name")

        status = ConnectorResponseConnectorStatus(d.pop("status"))

        created_at = isoparse(d.pop("createdAt"))

        def _parse_disabled_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                disabled_at_type_0 = isoparse(data)

                return disabled_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        disabled_at = _parse_disabled_at(d.pop("disabledAt"))

        uplink_path = d.pop("uplinkPath")

        connector_response_connector = cls(
            id=id,
            kind=kind,
            name=name,
            status=status,
            created_at=created_at,
            disabled_at=disabled_at,
            uplink_path=uplink_path,
        )

        connector_response_connector.additional_properties = d
        return connector_response_connector

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
