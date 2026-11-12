from enum import Enum


class ConnectorResponseConnectorKind(str, Enum):
    TTN = "ttn"

    def __str__(self) -> str:
        return str(self.value)
