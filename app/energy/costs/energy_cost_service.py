from dataclasses import dataclass
from zoneinfo import ZoneInfo
from datetime import date, datetime, timedelta

from app.octopus.costs.octopus_tariff_matching import (
    get_tariff_for_period,
    get_tariffs_for_period,
    match_tariff_from_periods,
    get_tariff_history,
)

UK_TZ = ZoneInfo("Europe/London")

IMPORT_TARIFF_CODE = "E-1R-INTELLI-FIX-12M-26-04-18-A"
EXPORT_TARIFF_CODE = "E-1R-OUTGOING-VAR-24-10-26-A"


@dataclass
class EnergyCostSummary:
    current_value_gbp_per_hour: float
    current_direction: str

    current_import_rate_p: float | None
    current_export_rate_p: float | None

    energy_import_kwh: float
    energy_export_kwh: float
    energy_net_kwh: float

    import_cost_gbp: float
    export_earnings_gbp: float
    net_cost_gbp: float

    unmatched_intervals: int


class EnergyCostService:
    """Calculate current energy costs and today's import/export totals."""

    def __init__(self, telemetry_repository):
        self.telemetry_repository = telemetry_repository

    @staticmethod
    def _latest_completed_bucket(now: datetime) -> datetime:
        """Return the start of the most recently completed 30-minute interval."""
        rounded_minute = (now.minute // 30) * 30

        current_bucket = now.replace(
            minute=rounded_minute,
            second=0,
            microsecond=0,
        )

        return current_bucket - timedelta(minutes=30)

    @staticmethod
    def _local_bucket_datetime(value: str) -> datetime:
        """Convert a database local-time bucket into an aware UK datetime."""
        local_naive = datetime.fromisoformat(value)

        if local_naive.tzinfo is not None:
            return local_naive.astimezone(UK_TZ)

        first = local_naive.replace(tzinfo=UK_TZ, fold=0)
        second = local_naive.replace(tzinfo=UK_TZ, fold=1)

        if first.utcoffset() != second.utcoffset():
            raise ValueError(
                f"Ambiguous local timestamp during DST change: {value}"
            )

        return first

    def get_current_rates(self, now: datetime | None = None) -> tuple[
        float | None, float | None
    ]:
        """Return the currently applicable import and export rates in p/kWh."""
        now = now or datetime.now(UK_TZ)

        import_tariff = get_tariff_for_period(
            IMPORT_TARIFF_CODE,
            now,
        )

        export_tariff = get_tariff_for_period(
            EXPORT_TARIFF_CODE,
            now,
        )

        import_rate = (
            import_tariff["rate_p_per_kwh"]
            if import_tariff else None
        )

        export_rate = (
            export_tariff["rate_p_per_kwh"]
            if export_tariff else None
        )

        return import_rate, export_rate

    def get_daily_summary(
        self,
        target_date: date | None = None,
        now: datetime | None = None,
    ) -> EnergyCostSummary:
        """Calculate energy and costs for a selected UK calendar day."""

        now = now or datetime.now(UK_TZ)

        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")

        now = now.astimezone(UK_TZ)
        target_date = target_date or now.date()

        midnight = datetime.combine(
            target_date,
            datetime.min.time(),
            tzinfo=UK_TZ,
        )

        if target_date > now.date():
            raise ValueError("target_date cannot be in the future")

        if target_date < now.date():
            latest_bucket = midnight + timedelta(days=1) - timedelta(minutes=30)
        else:
            latest_bucket = self._latest_completed_bucket(now)

        import_kwh = 0.0
        export_kwh = 0.0
        import_cost = 0.0
        export_earnings = 0.0
        unmatched = 0

        if latest_bucket >= midnight:
            rows = self.telemetry_repository.get_30m_history(
                midnight.strftime("%Y-%m-%d %H:%M:%S"),
                latest_bucket.strftime("%Y-%m-%d %H:%M:%S"),
            )

            period_end = latest_bucket + timedelta(minutes=30)

            import_tariffs = get_tariff_history(
                IMPORT_TARIFF_CODE,
                period_end,
            )
            
            export_tariffs = get_tariff_history(
                EXPORT_TARIFF_CODE,
                period_end,
            )

            for row in rows:
                try:
                    interval_start = self._local_bucket_datetime(row["bucket_start"])
                except ValueError:
                    unmatched += 1
                    continue

                grid_w = row["avg_grid_w"]

                if grid_w is None:
                    continue

                energy_kwh = abs(float(grid_w)) * 0.5 / 1000

                if grid_w < 0:
                    import_kwh += energy_kwh

                    tariff = match_tariff_from_periods(
                        import_tariffs,
                        interval_start,
                    )

                    if tariff is None:
                        unmatched += 1
                    else:
                        import_cost += energy_kwh * tariff["rate_p_per_kwh"] / 100

                elif grid_w > 0:
                    export_kwh += energy_kwh

                    tariff = match_tariff_from_periods(
                        export_tariffs,
                        interval_start,
                    )

                    if tariff is None:
                        unmatched += 1
                    else:
                        export_earnings += energy_kwh * tariff["rate_p_per_kwh"] / 100

        current_import_rate, current_export_rate = self.get_current_rates(now)

        latest_snapshot = self.telemetry_repository.get_latest_snapshot()

        current_value = 0.0
        current_direction = "neutral"

        if latest_snapshot is not None:
            grid_w = latest_snapshot["grid_w"] or 0.0

            if grid_w < 0:
                current_direction = "import"
                if current_import_rate is not None:
                    current_value = abs(grid_w) * current_import_rate / 100_000

            elif grid_w > 0:
                current_direction = "export"
                if current_export_rate is not None:
                    current_value = abs(grid_w) * current_export_rate / 100_000

        return EnergyCostSummary(
            current_value_gbp_per_hour=current_value,
            current_direction=current_direction,
            current_import_rate_p=current_import_rate,
            current_export_rate_p=current_export_rate,
            energy_import_kwh=import_kwh,
            energy_export_kwh=export_kwh,
            energy_net_kwh=import_kwh - export_kwh,
            import_cost_gbp=import_cost,
            export_earnings_gbp=export_earnings,
            net_cost_gbp=import_cost - export_earnings,
            unmatched_intervals=unmatched,
        )