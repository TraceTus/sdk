from enum import Enum


class ConnectorDeviceResponseEnvLabel(str, Enum):
    MAINNET = "mainnet"
    SIMULATION = "simulation"
    TESTNET = "testnet"

    def __str__(self) -> str:
        return str(self.value)
