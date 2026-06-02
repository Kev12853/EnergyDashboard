# app/backend/automation/repository.py

from datetime import datetime

from app.backend.automation.models import (
    AutomationRule,
)


class AutomationRepository:

    def __init__(
        self,
        connection,
    ):

        self.connection = connection

    def save_rule(
        self,
        rule: AutomationRule,
    ):

        self.connection.execute(
            """
            DELETE FROM automation_rules
            """
        )

        self.connection.execute(
            """
            INSERT INTO automation_rules (

                name,
                enabled,
                start_time,
                end_time,
                action,
                updated_at

            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rule.name,
                int(rule.enabled),
                rule.start_time,
                rule.end_time,
                rule.action,
                rule.updated_at.isoformat(),
            ),
        )

        self.connection.commit()

    def get_rule(
        self,
    ) -> AutomationRule | None:

        row = self.connection.execute(
            """
            SELECT *

            FROM automation_rules

            LIMIT 1
            """
        ).fetchone()

        if row is None:
            return None

        return AutomationRule(

            id=row["id"],

            name=row["name"],

            enabled=bool(
                row["enabled"]
            ),

            start_time=row["start_time"],

            end_time=row["end_time"],

            action=row["action"],

            updated_at=(
                datetime.fromisoformat(
                    row["updated_at"]
                )
            ),
        )
