from datetime import datetime

import pandas as pd

from app.backend.storage.db import (
    get_connection,
)


# =====================================================
# DISPATCHES
# =====================================================


def upsert_dispatches(
    dispatch_df: pd.DataFrame,
):

    if dispatch_df.empty:
        return

    conn = get_connection()

    now = datetime.utcnow().isoformat()

    for _, row in dispatch_df.iterrows():
        conn.execute(
            """
            INSERT INTO
            octopus_dispatches (

                dispatch_start,
                dispatch_end,
                scheduled_energy_kwh,
                status,
                last_seen

            )

            VALUES (

                ?, ?, ?, ?, ?

            )

            ON CONFLICT(

                dispatch_start,
                dispatch_end,
                status

            )

            DO UPDATE SET

                scheduled_energy_kwh =
                    excluded.scheduled_energy_kwh,

                last_seen =
                    excluded.last_seen
            """,
            (
                row["dispatch_start"].isoformat(),
                row["dispatch_end"].isoformat(),
                row["scheduled_energy_kwh"],
                row["status"],
                now,
            ),
        )

    conn.commit()

    conn.close()


def get_dispatch_history(
    days=7,
):

    conn = get_connection()

    query = f"""
    SELECT *

    FROM octopus_dispatches

    WHERE

        dispatch_start >=
        datetime(
            'now',
            '-{days} days'
        )

    ORDER BY

        dispatch_start DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
    )

    conn.close()

    if not df.empty:
        df["dispatch_start"] = pd.to_datetime(df["dispatch_start"])

        df["dispatch_end"] = pd.to_datetime(df["dispatch_end"])

        df["last_seen"] = pd.to_datetime(df["last_seen"])

    return df


# =====================================================
# TARIFFS
# =====================================================


def upsert_tariffs(
    tariff_df,
):

    if tariff_df.empty:
        return 0

    conn = get_connection()

    rows_added = 0

    for _, row in tariff_df.iterrows():
        result = conn.execute(
            """
            INSERT OR IGNORE INTO
            octopus_tariffs (

                tariff_code,

                slot_start,

                slot_end,

                unit_rate_gbp_per_kwh,

                created_at

            )

            VALUES (

                ?, ?, ?, ?, ?

            )
            """,
            (
                row["tariff_code"],
                row["slot_start"],
                row["slot_end"],
                row["unit_rate_gbp_per_kwh"],
                row["created_at"],
            ),
        )

        if result.rowcount:
            rows_added += 1

    conn.commit()

    conn.close()

    return rows_added


def get_recent_tariffs():

    conn = get_connection()

    query = """
    SELECT *

    FROM octopus_tariffs

    ORDER BY

        tariff_code,

        slot_start
    """

    df = pd.read_sql_query(
        query,
        conn,
    )

    conn.close()

    return df


def get_all_tariffs():

    conn = get_connection()

    query = """
    SELECT *

    FROM octopus_tariffs

    ORDER BY

        tariff_code,

        slot_start
    """

    df = pd.read_sql_query(
        query,
        conn,
    )

    conn.close()

    return df
