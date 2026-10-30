"""Shared service names and heartbeat freshness thresholds.

The SolaX poller and control service use these identifiers for their SQLite
heartbeat records; other application processes share the same enums.
"""

from enum import StrEnum, IntEnum


class ServiceName(StrEnum):
    """Stable service_heartbeat keys used by poller, control, aggregator and other application processes."""
    POLLER = "Poller"
    CONTROL = "SolaX Control"
    AGGREGATOR = "Aggregator"
    OCTOPUS = "Octopus"
    DASHBOARD = "Dashboard"
    DATABASE = "Database"


class HeartbeatAge(IntEnum):
    """Maximum accepted heartbeat ages in seconds for the named services; health/status consumers use these thresholds to detect stale processes."""
    POLLER = 60,
    CONTROL = 60,
    AGGREGATOR = 600,
    OCTOPUS = 7200,
    DATABASE = 800,


class ServiceState(IntEnum):
    """Integer state codes used to represent a service as running, warning or stopped."""
    RUNNING = 0
    WARNING = 1
    STOPPED = 2
