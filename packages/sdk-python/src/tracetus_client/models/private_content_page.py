from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.private_content_page_env_label import PrivateContentPageEnvLabel

if TYPE_CHECKING:
    from ..models.private_content_page_contents_item import PrivateContentPageContentsItem


T = TypeVar("T", bound="PrivateContentPage")


@_attrs_define
class PrivateContentPage:
    """
    Attributes:
        env_label (PrivateContentPageEnvLabel):  Example: simulation.
        contents (list[PrivateContentPageContentsItem]):
        next_cursor (None | str): Pass it as `cursor` for the next page; null on the last one.
    """

    env_label: PrivateContentPageEnvLabel
    contents: list[PrivateContentPageContentsItem]
    next_cursor: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        contents = []
        for contents_item_data in self.contents:
            contents_item = contents_item_data.to_dict()
            contents.append(contents_item)

        next_cursor: None | str
        next_cursor = self.next_cursor

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "contents": contents,
                "nextCursor": next_cursor,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.private_content_page_contents_item import PrivateContentPageContentsItem

        d = dict(src_dict)
        env_label = PrivateContentPageEnvLabel(d.pop("envLabel"))

        contents = []
        _contents = d.pop("contents")
        for contents_item_data in _contents:
            contents_item = PrivateContentPageContentsItem.from_dict(contents_item_data)

            contents.append(contents_item)

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        private_content_page = cls(
            env_label=env_label,
            contents=contents,
            next_cursor=next_cursor,
        )

        private_content_page.additional_properties = d
        return private_content_page

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
