from enum import Enum


class VerifyResponseAnchorsItemStatus(str, Enum):
    CONFIRMED = "confirmed"
    FAILED = "failed"
    PENDING = "pending"
    SUBMITTED = "submitted"

    def __str__(self) -> str:
        return str(self.value)
