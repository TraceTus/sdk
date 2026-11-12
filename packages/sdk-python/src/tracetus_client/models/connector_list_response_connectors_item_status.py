from enum import Enum


class ConnectorListResponseConnectorsItemStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"

    def __str__(self) -> str:
        return str(self.value)
