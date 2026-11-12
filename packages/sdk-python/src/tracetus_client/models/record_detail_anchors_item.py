from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse
from typing_extensions import Self

from ..models.record_detail_anchors_item_env_label import RecordDetailAnchorsItemEnvLabel
from ..models.record_detail_anchors_item_network import RecordDetailAnchorsItemNetwork
from ..models.record_detail_anchors_item_status import RecordDetailAnchorsItemStatus

T = TypeVar("T", bound="RecordDetailAnchorsItem")


@_attrs_define
class RecordDetailAnchorsItem:
    """
    Attributes:
        network (RecordDetailAnchorsItemNetwork):
        env_label (RecordDetailAnchorsItemEnvLabel):  Example: simulation.
        status (RecordDetailAnchorsItemStatus):
        tx_hash (None | str):
        block_number (None | str): Block number as text: it does not fit a JavaScript number.
        confirmed_at (datetime.datetime | None):
    """

    network: RecordDetailAnchorsItemNetwork
    env_label: RecordDetailAnchorsItemEnvLabel
    status: RecordDetailAnchorsItemStatus
    tx_hash: None | str
    block_number: None | str
    confirmed_at: datetime.datetime | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        network = self.network.value

        env_label = self.env_label.value

        status = self.status.value

        tx_hash: None | str
        tx_hash = self.tx_hash

        block_number: None | str
        block_number = self.block_number

        confirmed_at: None | str
        if isinstance(self.confirmed_at, datetime.datetime):
            confirmed_at = self.confirmed_at.isoformat()
        else:
            confirmed_at = self.confirmed_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "network": network,
                "envLabel": env_label,
                "status": status,
                "txHash": tx_hash,
                "blockNumber": block_number,
                "confirmedAt": confirmed_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        network = RecordDetailAnchorsItemNetwork(d.pop("network"))

        env_label = RecordDetailAnchorsItemEnvLabel(d.pop("envLabel"))

        status = RecordDetailAnchorsItemStatus(d.pop("status"))

        def _parse_tx_hash(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        tx_hash = _parse_tx_hash(d.pop("txHash"))

        def _parse_block_number(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        block_number = _parse_block_number(d.pop("blockNumber"))

        def _parse_confirmed_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                confirmed_at_type_0 = isoparse(data)

                return confirmed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        confirmed_at = _parse_confirmed_at(d.pop("confirmedAt"))

        record_detail_anchors_item = cls(
            network=network,
            env_label=env_label,
            status=status,
            tx_hash=tx_hash,
            block_number=block_number,
            confirmed_at=confirmed_at,
        )

        record_detail_anchors_item.additional_properties = d
        return record_detail_anchors_item

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
