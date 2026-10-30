from enum import StrEnum, IntEnum


class ServiceName(StrEnum):
    POLLER = "Poller"
    CONTROL = "SolaX Control"
    AGGREGATOR = "Aggregator"
    OCTOPUS = "Octopus"
    DASHBOARD = "Dashboard"
    DATABASE = "Database"


class HeartbeatAge(IntEnum):
    POLLER = 60,
    CONTROL = 60,
    AGGREGATOR = 600,
    OCTOPUS = 7200,
    DATABASE = 800,


class ServiceState(IntEnum):
    RUNNING = 0
    WARNING = 1
    STOPPED = 2
