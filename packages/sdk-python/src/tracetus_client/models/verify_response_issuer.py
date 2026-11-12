from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

T = TypeVar("T", bound="VerifyResponseIssuer")


@_attrs_define
class VerifyResponseIssuer:
    """Issuer, a legal entity. A natural person never appears in the verifier.

    Attributes:
        legal_name (str):
        city (None | str):
        country (str): ISO 3166-1 alpha-2
    """

    legal_name: str
    city: None | str
    country: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        legal_name = self.legal_name

        city: None | str
        city = self.city

        country = self.country

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "legalName": legal_name,
                "city": city,
                "country": country,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        legal_name = d.pop("legalName")

        def _parse_city(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        city = _parse_city(d.pop("city"))

        country = d.pop("country")

        verify_response_issuer = cls(
            legal_name=legal_name,
            city=city,
            country=country,
        )

        verify_response_issuer.additional_properties = d
        return verify_response_issuer

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
