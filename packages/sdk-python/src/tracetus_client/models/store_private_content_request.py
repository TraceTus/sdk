from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse
from typing_extensions import Self

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.store_private_content_request_content import StorePrivateContentRequestContent


T = TypeVar("T", bound="StorePrivateContentRequest")


@_attrs_define
class StorePrivateContentRequest:
    """
    Attributes:
        content (StorePrivateContentRequestContent): Content that stays with us, encrypted with your key. It never
            reaches a record, a log, a URL, a webhook, the public verifier or the network: the record carries the identifier
            of this content instead.
        purpose (str): Purpose the issuer declares for keeping this content, as a code of its own. It is what the LGPD
            requires recorded and what bounds the reading. Example: device-location.
        retention_until (datetime.date | Unset): Date the content is erased on, at the latest. Defaults to 365 days from
            now and goes no further than 3650 days. Example: 2027-11-11.
    """

    content: StorePrivateContentRequestContent
    purpose: str
    retention_until: datetime.date | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content = self.content.to_dict()

        purpose = self.purpose

        retention_until: str | Unset = UNSET
        if not isinstance(self.retention_until, Unset):
            retention_until = self.retention_until.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
                "purpose": purpose,
            }
        )
        if retention_until is not UNSET:
            field_dict["retentionUntil"] = retention_until

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.store_private_content_request_content import StorePrivateContentRequestContent

        d = dict(src_dict)
        content = StorePrivateContentRequestContent.from_dict(d.pop("content"))

        purpose = d.pop("purpose")

        _retention_until = d.pop("retentionUntil", UNSET)
        retention_until: datetime.date | Unset
        if isinstance(_retention_until, Unset):
            retention_until = UNSET
        else:
            retention_until = isoparse(_retention_until).date()

        store_private_content_request = cls(
            content=content,
            purpose=purpose,
            retention_until=retention_until,
        )

        store_private_content_request.additional_properties = d
        return store_private_content_request

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
