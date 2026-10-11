from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

FAULT_AFTER_FAILURES = 3
DEGRADED_AFTER_SECONDS = 5 * 60
FAULT_AFTER_SECONDS = 30 * 60


class HealthStatus(Enum):
    UNKNOWN = "unknown"
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAULT = "fault"


class IndicatorStatus(Enum):
    UNKNOWN = "unknown"
    OK = "ok"
    WARNING = "warning"
    FAULT = "fault"


@dataclass
class SystemHealth:
    last_snapshot_time: datetime | str | None = None
    last_successful_poll: datetime | str | None = None
    consecutive_failures: int = 0
    last_error: str | None = None
    scheduler_running: bool | None = None

    @property
    def data_age_seconds(
            self,
    ):

        last_snapshot_time = _to_datetime(self.last_snapshot_time)

        if last_snapshot_time is None:
            return None

        return (
                datetime.now(timezone.utc) - last_snapshot_time
        ).total_seconds()

    @property
    def data_status(self):

        age = self.data_age_seconds

        if age is None:
            return IndicatorStatus.UNKNOWN

        if age >= FAULT_AFTER_SECONDS:
            return IndicatorStatus.FAULT

        if age >= DEGRADED_AFTER_SECONDS:
            return IndicatorStatus.WARNING

        return IndicatorStatus.OK

    @property
    def overall_status(
            self,
    ):

        if self.last_snapshot_time is None:
            return HealthStatus.UNKNOWN

        if self.consecutive_failures >= FAULT_AFTER_FAILURES:
            return HealthStatus.FAULT

        data_age_seconds = self.data_age_seconds

        if data_age_seconds is None:
            return HealthStatus.UNKNOWN

        if data_age_seconds >= FAULT_AFTER_SECONDS:
            return HealthStatus.FAULT

        if data_age_seconds >= DEGRADED_AFTER_SECONDS:
            return HealthStatus.DEGRADED

        return HealthStatus.OPERATIONAL

    @property
    def poller_icon(self):

        return self._icon(self.poller_status)

    @property
    def poller_label(self):

        return self._label(self.poller_status)

    @property
    def poller_status(self):

        if self.last_successful_poll is None:
            return IndicatorStatus.UNKNOWN

        if self.consecutive_failures >= FAULT_AFTER_FAILURES:
            return IndicatorStatus.FAULT

        if self.consecutive_failures > 0:
            return IndicatorStatus.WARNING

        return IndicatorStatus.OK

    @property
    def system_icon(self):

        mapping = {
            HealthStatus.UNKNOWN: "⚫",
            HealthStatus.OPERATIONAL: "🟢",
            HealthStatus.DEGRADED: "🟡",
            HealthStatus.FAULT: "🔴",
        }

        return mapping[self.overall_status]

    @property
    def system_label(self):

        mapping = {
            HealthStatus.UNKNOWN: "Unknown",
            HealthStatus.OPERATIONAL: "Healthy",
            HealthStatus.DEGRADED: "Delayed",
            HealthStatus.FAULT: "Offline",
        }

        return mapping[self.overall_status]

    @property
    def data_icon(self):

        return self._icon(self.data_status)

    @property
    def data_label(self):

        return self._label(self.data_status)

    @property
    def data_age_text(self):

        age = self.data_age_seconds

        if age is None:
            return "Unknown"

        age = int(age)

        if age < 60:
            return f"{age} s"

        if age < 3600:
            return f"{age // 60} min"

        return f"{age // 3600} hr"

    @staticmethod
    def _icon(status):

        mapping = {
            IndicatorStatus.UNKNOWN: "⚫",
            IndicatorStatus.OK: "🟢",
            IndicatorStatus.WARNING: "🟡",
            IndicatorStatus.FAULT: "🔴",
        }

        return mapping[status]


    @staticmethod
    def _label(status):

        mapping = {
            IndicatorStatus.UNKNOWN: "Unknown",
            IndicatorStatus.OK: "Healthy",
            IndicatorStatus.WARNING: "Delayed",
            IndicatorStatus.FAULT: "Offline",
        }

        return mapping[status]

def get_system_health(
        last_snapshot_time=None,
        last_successful_poll=None,
        consecutive_failures=0,
        last_error=None,
        scheduler_running=None,
):
    return SystemHealth(
        last_snapshot_time=last_snapshot_time,
        last_successful_poll=last_successful_poll,
        consecutive_failures=consecutive_failures,
        last_error=last_error,
        scheduler_running=scheduler_running,
    )


def _to_datetime(
        value,
):
    if value is None:
        return None

    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()

    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)
