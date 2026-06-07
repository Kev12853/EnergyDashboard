from dataclasses import dataclass
from datetime import datetime, time


@dataclass
class SchedulePeriod:
    id: int | None
    name: str
    source: str
    enabled: bool
    start_time: str
    end_time: str
    mode: str
    priority: int
    updated_at: datetime


@dataclass
class AutomationState:
    active: bool
    actioned: bool
    period_name: str | None
    mode: str | None
    start_time: time | None
    end_time: time | None
    status: str
    message: str