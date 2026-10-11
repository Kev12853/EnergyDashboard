from datetime import datetime

from app.solax.backend.automation.models import SchedulePeriod


class AutomationRepository:

    def __init__(self, connection) -> None:

        self.connection = connection

    def get_periods(self) -> list[SchedulePeriod]:

        rows = self.connection.execute(
            """
            SELECT *
            FROM schedule_periods
            ORDER BY priority DESC,
                     start_time
            """
        ).fetchall()

        return [
            SchedulePeriod(
                id=row["id"],
                name=row["name"],
                source=row["source"],
                enabled=bool(row["enabled"]),
                start_time=row["start_time"],
                end_time=row["end_time"],
                mode=row["mode"],
                priority=row["priority"],
                updated_at=datetime.fromisoformat(
                    row["updated_at"]
                ),
            )
            for row in rows
        ]