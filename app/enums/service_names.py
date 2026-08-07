from enum import StrEnum


class ServiceName(StrEnum):
    POLLER = "Poller"
    AGGREGATOR = "Aggregator"
    OCTOPUS = "Octopus"
    DASHBOARD = "Dashboard"