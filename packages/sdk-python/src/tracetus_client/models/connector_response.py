from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.connector_response_env_label import ConnectorResponseEnvLabel

if TYPE_CHECKING:
    from ..models.connector_response_connector import ConnectorResponseConnector


T = TypeVar("T", bound="ConnectorResponse")


@_attrs_define
class ConnectorResponse:
    """
    Attributes:
        env_label (ConnectorResponseEnvLabel):  Example: simulation.
        connector (ConnectorResponseConnector):
    """

    env_label: ConnectorResponseEnvLabel
    connector: ConnectorResponseConnector
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        connector = self.connector.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "connector": connector,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.connector_response_connector import ConnectorResponseConnector

        d = dict(src_dict)
        env_label = ConnectorResponseEnvLabel(d.pop("envLabel"))

        connector = ConnectorResponseConnector.from_dict(d.pop("connector"))

        connector_response = cls(
            env_label=env_label,
            connector=connector,
        )

        connector_response.additional_properties = d
        return connector_response

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
