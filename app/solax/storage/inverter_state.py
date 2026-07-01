from datetime import datetime

from app.enums.inverter_state_enums import InverterRequestPhase


def get_inverter_state(
    connection,
):
    cursor = connection.execute(
        """
        SELECT
            requested_work_mode,
            requested_manual_mode,
            restore_work_mode_to,
            restore_manual_mode_to,
            active,
            source

        FROM inverter_state

        LIMIT 1
        """
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return {
        "requested_work_mode": row[0],
        "requested_manual_mode": row[1],
        "restore_work_mode_to": row[2],
        "restore_manual_mode_to": row[3],
        "active": row[4],
        "source": row[5],
    }


def request_restore(connection):
    """
    Request restoration of the operating mode that was active
    before the temporary override began.

    Copies the remembered operating mode into the requested
    operating mode and clears the stored restore state.
    """

    connection.execute(
        """
        UPDATE inverter_state

        SET
            requested_work_mode = restore_work_mode_to,
            requested_manual_mode = restore_manual_mode_to,

            phase = ?,

            active = 1

        WHERE id = 1
        """,
        (InverterRequestPhase.RESTORE,),
    )

    connection.commit()


def set_inverter_state(
    connection,
    requested_work_mode,
    requested_manual_mode,
    restore_work_mode_to,
    restore_manual_mode_to,
    phase,
    active,
    source,
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
                requested_work_mode,
                requested_manual_mode,
                restore_work_mode_to,
                restore_manual_mode_to,
                active,
                source

            )

            VALUES (

                1,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?

            )
            """,
            (
                requested_work_mode,
                requested_manual_mode,
                restore_work_mode_to,
                restore_manual_mode_to,
                active,
                source
            ),
        )

    else:
        connection.execute(
            """
            UPDATE inverter_state

            SET
                requested_work_mode = ?,
                requested_manual_mode = ?,
                restore_work_mode_to = ?,
                restore_manual_mode_to = ?,
                active = ?,
                source = ?

            WHERE id = 1
            """,
            (
                requested_work_mode,
                requested_manual_mode,
                restore_work_mode_to,
                restore_manual_mode_to,
                active,
                source,
            ),
        )

    connection.commit()


def clear_inverter_state(connection):
    connection.execute(
        """
        UPDATE inverter_state

        SET
            requested_work_mode = NULL,
            requested_manual_mode = NULL,
            restore_work_mode_to = NULL,
            restore_manual_mode_to = NULL,
            active = 0,
            source = NULL

        WHERE id = 1
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


