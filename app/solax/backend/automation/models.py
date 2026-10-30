"""Define typed schedule and automation-status data returned by the scheduler and repositories. These models contain state only and have no I/O side effects."""

from dataclasses import dataclass
from datetime import datetime, time

from app.enums.automation_enums import InverterWorkMode


@dataclass
class SchedulePeriod:
    """Represent one stored schedule window, including ownership/source, requested mode, priority and update timestamp."""
    id: int | None
    name: str
    source: str
    enabled: bool
    start_time: str
    end_time: str
    mode: InverterWorkMode
    priority: int
    updated_at: datetime


@dataclass
class AutomationState:
    """Represent the scheduler status shown to callers; this is descriptive state, not confirmation of the inverter mode."""
    active: bool
    actioned: bool
    period_name: str | None
    mode: str | None
    start_time: time | None
    end_time: time | None
    status: str
    message: str