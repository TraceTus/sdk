from enum import Enum


class PrivateContentWithContentContentStatus(str, Enum):
    ERASED = "erased"
    STORED = "stored"

    def __str__(self) -> str:
        return str(self.value)
