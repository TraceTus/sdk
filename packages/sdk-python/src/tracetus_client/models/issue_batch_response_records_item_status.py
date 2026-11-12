from enum import Enum


class IssueBatchResponseRecordsItemStatus(str, Enum):
    ANCHORED = "anchored"
    BATCHED = "batched"
    PENDING = "pending"
    REVOKED = "revoked"

    def __str__(self) -> str:
        return str(self.value)
