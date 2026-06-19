from datetime import datetime


def get_inverter_state(
    connection,
):
    cursor = connection.execute(
        """
        SELECT

            desired_work_mode,
            desired_manual_mode,
            source,
            updated_at

        FROM inverter_state

        LIMIT 1
        """
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return {
        "work_mode": row[0],
        "manual_mode": row[1],
        "source": row[2],
        "updated_at": row[3],
    }


def set_inverter_state(
    connection,
    work_mode,
    manual_mode=None,
    source="scheduler",
):
    existing = get_inverter_state(
        connection,
    )

    timestamp = datetime.now().isoformat()

    if existing is None:
        connection.execute(
            """
            INSERT INTO inverter_state (

                id,
                desired_work_mode,
                desired_manual_mode,
                source,
                updated_at

            )

            VALUES (

                1,
                ?,
                ?,
                ?,
                ?

            )
            """,
            (
                work_mode,
                manual_mode,
                source,
                timestamp,
            ),
        )

    else:
        connection.execute(
            """
            UPDATE inverter_state

            SET

                desired_work_mode = ?,
                desired_manual_mode = ?,
                source = ?,
                updated_at = ?

            WHERE id = 1
            """,
            (
                work_mode,
                manual_mode,
                source,
                timestamp,
            ),
        )

    connection.commit()


def clear_inverter_state(
    connection,
):
    connection.execute(
        """
        DELETE FROM inverter_state
        """
    )

    connection.commit()


def has_pending_inverter_state(
    connection,
):
    return (
        get_inverter_state(
            connection,
        )
        is not None
    )