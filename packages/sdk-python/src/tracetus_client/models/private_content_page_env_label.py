from enum import Enum


class PrivateContentPageEnvLabel(str, Enum):
    MAINNET = "mainnet"
    SIMULATION = "simulation"
    TESTNET = "testnet"

    def __str__(self) -> str:
        return str(self.value)
