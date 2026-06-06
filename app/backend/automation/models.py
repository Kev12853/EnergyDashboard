from dataclasses import dataclass
from datetime import datetime


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
