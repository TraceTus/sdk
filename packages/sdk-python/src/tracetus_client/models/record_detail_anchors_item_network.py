from enum import Enum


class RecordDetailAnchorsItemNetwork(str, Enum):
    PUBLIC_ANCHOR = "public_anchor"
    RBB = "rbb"

    def __str__(self) -> str:
        return str(self.value)
