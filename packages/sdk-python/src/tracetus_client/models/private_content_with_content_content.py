from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse
from typing_extensions import Self

from ..models.private_content_with_content_content_status import (
    PrivateContentWithContentContentStatus,
)

if TYPE_CHECKING:
    from ..models.private_content_with_content_content_content import (
        PrivateContentWithContentContentContent,
    )


T = TypeVar("T", bound="PrivateContentWithContentContent")


@_attrs_define
class PrivateContentWithContentContent:
    """
    Attributes:
        id (str):
        purpose (str): Purpose the issuer declares for keeping this content, as a code of its own. It is what the LGPD
            requires recorded and what bounds the reading. Example: device-location.
        status (PrivateContentWithContentContentStatus): `stored` while the content can be read. `erased` once it
            cannot: either you erased it, or its retention date has passed — a listing never shows as stored something a
            read would refuse.
        retention_until (datetime.date):
        created_at (datetime.datetime):
        erased_at (datetime.datetime | None): When the content was dropped. Null while it is still there, and also while
            its retention date has passed and the retention routine has not come round yet.
        content (PrivateContentWithContentContentContent): Content that stays with us, encrypted with your key. It never
            reaches a record, a log, a URL, a webhook, the public verifier or the network: the record carries the identifier
            of this content instead.
    """

    id: str
    purpose: str
    status: PrivateContentWithContentContentStatus
    retention_until: datetime.date
    created_at: datetime.datetime
    erased_at: datetime.datetime | None
    content: PrivateContentWithContentContentContent
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        purpose = self.purpose

        status = self.status.value

        retention_until = self.retention_until.isoformat()

        created_at = self.created_at.isoformat()

        erased_at: None | str
        if isinstance(self.erased_at, datetime.datetime):
            erased_at = self.erased_at.isoformat()
        else:
            erased_at = self.erased_at

        content = self.content.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "purpose": purpose,
                "status": status,
                "retentionUntil": retention_until,
                "createdAt": created_at,
                "erasedAt": erased_at,
                "content": content,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.private_content_with_content_content_content import (
            PrivateContentWithContentContentContent,
        )

        d = dict(src_dict)
        id = d.pop("id")

        purpose = d.pop("purpose")

        status = PrivateContentWithContentContentStatus(d.pop("status"))

        retention_until = isoparse(d.pop("retentionUntil")).date()

        created_at = isoparse(d.pop("createdAt"))

        def _parse_erased_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                erased_at_type_0 = isoparse(data)

                return erased_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        erased_at = _parse_erased_at(d.pop("erasedAt"))

        content = PrivateContentWithContentContentContent.from_dict(d.pop("content"))

        private_content_with_content_content = cls(
            id=id,
            purpose=purpose,
            status=status,
            retention_until=retention_until,
            created_at=created_at,
            erased_at=erased_at,
            content=content,
        )

        private_content_with_content_content.additional_properties = d
        return private_content_with_content_content

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
