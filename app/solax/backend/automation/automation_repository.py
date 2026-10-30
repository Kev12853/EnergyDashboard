"""Read and write scheduled automation periods in SQLite. The repository supplies schedule data to Scheduler and does not issue Modbus commands."""

# app/backend/automation/solax_repository.py

from datetime import datetime

from app.solax.backend.automation.models import (
    SchedulePeriod,
)


class ScheduleRepository:
    """Access schedule_periods rows in SQLite; this repository commits mutations and performs no inverter I/O."""
    def __init__(
        self,
        connection,
    ):
        self.connection = connection

    def save_period(
        self,
        period: SchedulePeriod,
    ):

        """Insert a new SchedulePeriod or update the row identified by its id; mutates the supplied model with the generated id and commits the transaction."""
        if period.id is None:
            cursor = self.connection.execute(
                """
                INSERT INTO schedule_periods (

                    name,
                    source,
                    enabled,
                    start_time,
                    end_time,
                    mode,
                    priority,
                    updated_at

                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    period.name,
                    period.source,
                    int(period.enabled),
                    period.start_time,
                    period.end_time,
                    period.mode,
                    period.priority,
                    period.updated_at.isoformat(),
                ),
            )

            period.id = cursor.lastrowid

        else:
            self.connection.execute(
                """
                UPDATE schedule_periods

                SET

                    name = ?,
                    source = ?,
                    enabled = ?,
                    start_time = ?,
                    end_time = ?,
                    mode = ?,
                    priority = ?,
                    updated_at = ?

                WHERE id = ?
                """,
                (
                    period.name,
                    period.source,
                    int(period.enabled),
                    period.start_time,
                    period.end_time,
                    period.mode,
                    period.priority,
                    period.updated_at.isoformat(),
                    period.id,
                ),
            )

        self.connection.commit()

    def get_period(
        self,
        period_id: int,
    ) -> SchedulePeriod | None:

        """Fetch one schedule_periods row by id and return a SchedulePeriod, or None when it does not exist."""
        row = self.connection.execute(
            """
            SELECT *

            FROM schedule_periods

            WHERE id = ?
            """,
            (period_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_period(row)

    def get_periods(
        self,
    ) -> list[SchedulePeriod]:

        """Return schedule_periods ordered by descending priority and then start time; performs a read only."""
        rows = self.connection.execute(
            """
            SELECT *

            FROM schedule_periods

            ORDER BY priority DESC,
                     start_time
            """
        ).fetchall()

        return [self._row_to_period(row) for row in rows]

    def delete_period(
        self,
        period_id: int,
    ):

        """Delete the schedule_periods row with the supplied id and commit the change."""
        self.connection.execute(
            """
            DELETE FROM schedule_periods

            WHERE id = ?
            """,
            (period_id,),
        )

        self.connection.commit()

    @staticmethod
    def _row_to_period(
        row,
    ) -> SchedulePeriod:

        return SchedulePeriod(
            id=row["id"],
            name=row["name"],
            source=row["source"],
            enabled=bool(row["enabled"]),
            start_time=row["start_time"],
            end_time=row["end_time"],
            mode=row["mode"],
            priority=row["priority"],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def get_rule(
        self,
    ) -> SchedulePeriod | None:

        """Return the first period in repository order, or None when no schedule exists."""
        periods = self.get_periods()

        return periods[0] if periods else None
