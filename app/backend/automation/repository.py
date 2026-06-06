# app/backend/automation/repository.py

from datetime import datetime

from app.backend.automation.models import (
    SchedulePeriod,
)


class AutomationRepository:

    def __init__(
        self,
        connection,
    ):
        self.connection = connection

    def save_period(
        self,
        period: SchedulePeriod,
    ):

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

        return self._row_to_period(
            row
        )
    def get_periods(
        self,
    ) -> list[SchedulePeriod]:

        rows = self.connection.execute(
            """
            SELECT *

            FROM schedule_periods

            ORDER BY priority DESC,
                     start_time
            """
        ).fetchall()

        return [
            self._row_to_period(row)
            for row in rows
        ]

    def delete_period(
        self,
        period_id: int,
    ):

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

            enabled=bool(
                row["enabled"]
            ),

            start_time=row["start_time"],

            end_time=row["end_time"],

            mode=row["mode"],

            priority=row["priority"],

            updated_at=datetime.fromisoformat(
                row["updated_at"]
            ),
        )

    def get_rule(
            self,
    ) -> SchedulePeriod | None:

        periods = self.get_periods()

        return periods[0] if periods else None