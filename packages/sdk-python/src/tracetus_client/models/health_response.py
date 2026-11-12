from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from typing_extensions import Self

from ..models.health_response_env_label import HealthResponseEnvLabel
from ..models.health_response_environment import HealthResponseEnvironment
from ..models.health_response_status import HealthResponseStatus

T = TypeVar("T", bound="HealthResponse")


@_attrs_define
class HealthResponse:
    """
    Attributes:
        status (HealthResponseStatus):
        env_label (HealthResponseEnvLabel):  Example: simulation.
        environment (HealthResponseEnvironment):  Example: sandbox.
    """

    status: HealthResponseStatus
    env_label: HealthResponseEnvLabel
    environment: HealthResponseEnvironment
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        env_label = self.env_label.value

        environment = self.environment.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "envLabel": env_label,
                "environment": environment,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        status = HealthResponseStatus(d.pop("status"))

        env_label = HealthResponseEnvLabel(d.pop("envLabel"))

        environment = HealthResponseEnvironment(d.pop("environment"))

        health_response = cls(
            status=status,
            env_label=env_label,
            environment=environment,
        )

        health_response.additional_properties = d
        return health_response

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
