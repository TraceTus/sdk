from enum import Enum


class CreateConnectorResponseEnvLabel(str, Enum):
    MAINNET = "mainnet"
    SIMULATION = "simulation"
    TESTNET = "testnet"

    def __str__(self) -> str:
        return str(self.value)
