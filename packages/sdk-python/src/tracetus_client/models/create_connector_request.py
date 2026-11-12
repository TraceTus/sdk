from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.create_connector_request_kind import CreateConnectorRequestKind

T = TypeVar("T", bound="CreateConnectorRequest")


@_attrs_define
class CreateConnectorRequest:
    """
    Attributes:
        kind (CreateConnectorRequestKind): Kind of connector. The URL a network calls is derived from it. Example: ttn.
        name (str): Operational name of the connector, for whoever runs it. No personal data. Example: field oracle.
    """

    kind: CreateConnectorRequestKind
    name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kind = self.kind.value

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind": kind,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        kind = CreateConnectorRequestKind(d.pop("kind"))

        name = d.pop("name")

        create_connector_request = cls(
            kind=kind,
            name=name,
        )

        create_connector_request.additional_properties = d
        return create_connector_request

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
