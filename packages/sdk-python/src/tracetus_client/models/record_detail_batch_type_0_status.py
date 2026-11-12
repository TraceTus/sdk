from enum import Enum


class RecordDetailBatchType0Status(str, Enum):
    CONFIRMED = "confirmed"
    FAILED = "failed"
    OPEN = "open"
    SEALED = "sealed"
    SUBMITTED = "submitted"

    def __str__(self) -> str:
        return str(self.value)
