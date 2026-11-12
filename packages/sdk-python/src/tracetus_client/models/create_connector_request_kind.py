from enum import Enum


class CreateConnectorRequestKind(str, Enum):
    TTN = "ttn"

    def __str__(self) -> str:
        return str(self.value)
