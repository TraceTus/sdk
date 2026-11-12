from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.private_content_with_content_env_label import PrivateContentWithContentEnvLabel

if TYPE_CHECKING:
    from ..models.private_content_with_content_content import PrivateContentWithContentContent


T = TypeVar("T", bound="PrivateContentWithContent")


@_attrs_define
class PrivateContentWithContent:
    """
    Attributes:
        env_label (PrivateContentWithContentEnvLabel):  Example: simulation.
        content (PrivateContentWithContentContent):
    """

    env_label: PrivateContentWithContentEnvLabel
    content: PrivateContentWithContentContent
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
        from ..models.private_content_with_content_content import PrivateContentWithContentContent

        d = dict(src_dict)
        env_label = PrivateContentWithContentEnvLabel(d.pop("envLabel"))

        content = PrivateContentWithContentContent.from_dict(d.pop("content"))

        private_content_with_content = cls(
            env_label=env_label,
            content=content,
        )

        private_content_with_content.additional_properties = d
        return private_content_with_content

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
