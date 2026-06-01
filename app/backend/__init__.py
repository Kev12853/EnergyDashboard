from dataclasses import dataclass
from datetime import datetime


@dataclass
class AutomationRule:

    id: int | None

    name: str

    enabled: bool

    start_time: str

    end_time: str

    action: str

    last_executed_at: datetime | None

    updated_at: datetime