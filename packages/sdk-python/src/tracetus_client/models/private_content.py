from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.private_content_env_label import PrivateContentEnvLabel

if TYPE_CHECKING:
    from ..models.private_content_content import PrivateContentContent


T = TypeVar("T", bound="PrivateContent")


@_attrs_define
class PrivateContent:
    """
    Attributes:
        env_label (PrivateContentEnvLabel):  Example: simulation.
        content (PrivateContentContent):
    """

    env_label: PrivateContentEnvLabel
    content: PrivateContentContent
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        env_label = self.env_label.value

        content = self.content.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "envLabel": env_label,
                "content": content,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.private_content_content import PrivateContentContent

        d = dict(src_dict)
        env_label = PrivateContentEnvLabel(d.pop("envLabel"))

        content = PrivateContentContent.from_dict(d.pop("content"))

        private_content = cls(
            env_label=env_label,
            content=content,
        )

        private_content.additional_properties = d
        return private_content

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
