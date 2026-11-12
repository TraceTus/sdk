from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.connector_list_response_env_label import ConnectorListResponseEnvLabel

if TYPE_CHECKING:
    from ..models.connector_list_response_connectors_item import ConnectorListResponseConnectorsItem


T = TypeVar("T", bound="ConnectorListResponse")


@_attrs_define
class ConnectorListResponse:
    """
    Attributes:
        env_label (ConnectorListResponseEnvLabel):  Example: simulation.
        count (int):
        next_cursor (None | str): Pass it as `cursor` to read the next page. Null when this page is the last.
        connectors (list[ConnectorListResponseConnectorsItem]):
    """

    env_label: ConnectorListResponseEnvLabel
    count: int
    next_cursor: None | str
    connectors: list[ConnectorListResponseConnectorsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        count = self.count

        next_cursor: None | str
        next_cursor = self.next_cursor

        connectors = []
        for connectors_item_data in self.connectors:
            connectors_item = connectors_item_data.to_dict()
            connectors.append(connectors_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "count": count,
                "nextCursor": next_cursor,
                "connectors": connectors,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.connector_list_response_connectors_item import (
            ConnectorListResponseConnectorsItem,
        )

        d = dict(src_dict)
        env_label = ConnectorListResponseEnvLabel(d.pop("envLabel"))

        count = d.pop("count")

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        connectors = []
        _connectors = d.pop("connectors")
        for connectors_item_data in _connectors:
            connectors_item = ConnectorListResponseConnectorsItem.from_dict(connectors_item_data)

            connectors.append(connectors_item)

        connector_list_response = cls(
            env_label=env_label,
            count=count,
            next_cursor=next_cursor,
            connectors=connectors,
        )

        connector_list_response.additional_properties = d
        return connector_list_response

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
