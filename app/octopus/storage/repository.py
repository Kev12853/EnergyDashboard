import sqlite3
from datetime import datetime, timezone, time

import pandas as pd

from app.connections.connection import get_connection


class OctopusRepository:
    # =====================================================
    # DISPATCHES
    # =====================================================

    def upsert_dispatches(
        self,
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
                    first_seen,
                    last_seen

                )

                VALUES (

                    ?, ?, ?, ?, ?, ?

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
                    now,
                ),
            )

        conn.commit()
        conn.close()

    def get_dispatch_history(
        self,
        start_date,
        end_date,
    ):

        conn = get_connection()

        query = """
        SELECT *

        FROM octopus_dispatches

        WHERE
            dispatch_start >= ?
            AND dispatch_start < ?

        ORDER BY
            dispatch_start DESC
        """

        start_datetime = pd.Timestamp(start_date)

        end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1)

        df = pd.read_sql_query(
            query,
            conn,
            params=[
                start_datetime.isoformat(),
                end_datetime.isoformat(),
            ],
        )

        conn.close()

        if not df.empty:
            df["dispatch_start"] = pd.to_datetime(df["dispatch_start"])

            df["dispatch_end"] = pd.to_datetime(df["dispatch_end"])

            df["first_seen"] = pd.to_datetime(df["first_seen"])

            df["last_seen"] = pd.to_datetime(df["last_seen"])

        return df

    def get_current_dispatch_schedule(
        self,
        completed_hours: int = 24,
    ):

        conn = get_connection()

        now = pd.Timestamp.now()

        cutoff = now - pd.Timedelta(hours=completed_hours)

        query = """
        WITH latest_planned AS (

            SELECT
                MAX(last_seen) AS last_seen

            FROM
                octopus_dispatches

            WHERE
                status = 'Planned'
        )

        SELECT *

        FROM octopus_dispatches

        WHERE

            (
                status = 'Completed'

                AND dispatch_end >= ?
                AND dispatch_end <= ?
            )

            OR

            (
                status = 'Planned'

                AND dispatch_end >= ?

                AND last_seen = (
                    SELECT last_seen
                    FROM latest_planned
                )
            )

        ORDER BY
            dispatch_start
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=[
                cutoff.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ],
        )

        conn.close()

        if not df.empty:
            df["dispatch_start"] = pd.to_datetime(df["dispatch_start"])

            df["dispatch_end"] = pd.to_datetime(df["dispatch_end"])

            df["first_seen"] = pd.to_datetime(df["first_seen"])

            df["last_seen"] = pd.to_datetime(df["last_seen"])

        completed = df[df["status"] == "Completed"].copy()

        planned = df[df["status"] == "Planned"].copy()

        return completed, planned

    # =====================================================
    # TARIFFS
    # =====================================================

    def upsert_tariffs(
        self,
        tariff_df: pd.DataFrame,
        tariff_code: str,
    ) -> int:

        if tariff_df.empty:
            return 0

        conn = get_connection()

        rows_changed = 0

        created_at = datetime.now().isoformat()

        for _, row in tariff_df.iterrows():
            valid_to = row["valid_to"]

            # -------------------------------------------------
            # Open-ended tariff
            # -------------------------------------------------

            if pd.isna(valid_to):
                existing = conn.execute(
                    """
                    SELECT
                        id,
                        value_exc_vat,
                        value_inc_vat

                    FROM
                        octopus_tariffs

                    WHERE
                        tariff_code = ?

                        AND valid_from = ?

                        AND valid_to IS NULL
                    """,
                    (
                        tariff_code,
                        row["valid_from"],
                    ),
                ).fetchone()

                if existing is None:
                    conn.execute(
                        """
                        INSERT INTO
                        octopus_tariffs (

                            tariff_code,
                            value_exc_vat,
                            value_inc_vat,
                            valid_from,
                            valid_to,
                            payment_method,
                            created_at

                        )

                        VALUES (
                            ?, ?, ?, ?, ?, ?, ?
                        )
                        """,
                        (
                            tariff_code,
                            row["value_exc_vat"],
                            row["value_inc_vat"],
                            row["valid_from"],
                            None,
                            row["payment_method"],
                            created_at,
                        ),
                    )

                    rows_changed += 1

                else:
                    existing_id = existing[0]

                    existing_exc = existing[1]

                    existing_inc = existing[2]

                    if (
                        existing_exc != row["value_exc_vat"]
                        or existing_inc != row["value_inc_vat"]
                    ):
                        conn.execute(
                            """
                            UPDATE
                                octopus_tariffs

                            SET
                                value_exc_vat = ?,
                                value_inc_vat = ?,
                                payment_method = ?

                            WHERE
                                id = ?
                            """,
                            (
                                row["value_exc_vat"],
                                row["value_inc_vat"],
                                row["payment_method"],
                                existing_id,
                            ),
                        )

                        rows_changed += 1

            # -------------------------------------------------
            # Normal dated tariff period
            # -------------------------------------------------

            else:
                result = conn.execute(
                    """
                    INSERT INTO
                    octopus_tariffs (

                        tariff_code,
                        value_exc_vat,
                        value_inc_vat,
                        valid_from,
                        valid_to,
                        payment_method,
                        created_at

                    )

                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?
                    )

                    ON CONFLICT(
                        tariff_code,
                        valid_from,
                        valid_to
                    )

                    DO UPDATE SET

                        value_exc_vat =
                            excluded.value_exc_vat,

                        value_inc_vat =
                            excluded.value_inc_vat

                    WHERE
                        value_exc_vat !=
                            excluded.value_exc_vat

                        OR value_inc_vat !=
                            excluded.value_inc_vat
                    """,
                    (
                        tariff_code,
                        row["value_exc_vat"],
                        row["value_inc_vat"],
                        row["valid_from"],
                        row["valid_to"],
                        row["payment_method"],
                        created_at,
                    ),
                )

                if result.rowcount:
                    rows_changed += 1

        conn.commit()

        conn.close()

        return rows_changed


    def upsert_four_rate_tariffs(
        self,
        tariff_df: pd.DataFrame,
        tariff_code: str,
    ) -> int:

        if tariff_df.empty:
            return 0

        conn = get_connection()

        rows_changed = 0
        created_at = datetime.now().isoformat()

        for _, row in tariff_df.iterrows():
            result = conn.execute(
                """
                INSERT INTO
                octopus_four_rate_tariffs (

                    tariff_code,
                    rate_type,
                    value_exc_vat,
                    value_inc_vat,
                    valid_from,
                    valid_to,
                    payment_method,
                    created_at

                )

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?
                )

                ON CONFLICT(
                    tariff_code,
                    rate_type,
                    valid_from,
                    valid_to
                )

                DO UPDATE SET

                    value_exc_vat =
                        excluded.value_exc_vat,

                    value_inc_vat =
                        excluded.value_inc_vat,

                    payment_method =
                        excluded.payment_method

                WHERE
                    value_exc_vat !=
                        excluded.value_exc_vat

                    OR value_inc_vat !=
                        excluded.value_inc_vat

                    OR payment_method !=
                        excluded.payment_method
                """,
                (
                    tariff_code,
                    row["rate_type"],
                    row["value_exc_vat"],
                    row["value_inc_vat"],
                    row["valid_from"],
                    row["valid_to"],
                    row["payment_method"],
                    created_at,
                ),
            )

            if result.rowcount:
                rows_changed += 1

        conn.commit()
        conn.close()

        return rows_changed

    def upsert_agreements(
        self,
        agreements,
    ) -> int:

        if not agreements:
            return 0

        from app.config.octopus_config import (
            IMPORT_MPAN,
            EXPORT_MPAN,
        )

        conn = get_connection()

        rows_added = 0

        for agreement in agreements:
            mpan = agreement["mpan"]

            if mpan == IMPORT_MPAN:
                agreement_type = "import"

            elif mpan == EXPORT_MPAN:
                agreement_type = "export"

            else:
                continue

            result = conn.execute(
                """
                INSERT OR IGNORE INTO
                octopus_agreements (

                    account_number,
                    mpan,
                    agreement_type,
                    tariff_type,
                    product_code,
                    tariff_code,
                    valid_from,
                    valid_to,
                    created_at

                )
                VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
                """,
                (
                    agreement["account_number"],
                    mpan,
                    agreement_type,
                    agreement["tariff_type"],
                    agreement["product_code"],
                    agreement["tariff_code"],
                    agreement["valid_from"],
                    agreement["valid_to"],
                    datetime.now().isoformat(),
                ),
            )

            if result.rowcount:
                rows_added += 1

        conn.commit()
        conn.close()

        return rows_added

    def get_current_import_agreement(self) -> sqlite3.Row | None:
        conn = get_connection()

        now = pd.Timestamp.now(tz="UTC").isoformat()

        query = """
        SELECT
            *
        FROM
            octopus_agreements
        WHERE
            agreement_type = 'import'
            AND valid_from <= ?
            AND (
                valid_to IS NULL
                OR valid_to > ?
            )
        ORDER BY
            valid_from DESC
        LIMIT 1
        """

        row = conn.execute(
            query,
            (now, now),
        ).fetchone()

        conn.close()

        return row

    def get_current_import_tariff(self) -> str:

        row = self.get_current_import_agreement()

        if row is None:
            raise RuntimeError("No current import tariff agreement found")

        return row["tariff_code"]

    def get_comparison_import_tariff(self) -> str:
        conn = get_connection()

        now = pd.Timestamp.now(tz="UTC").isoformat()

        query = """
        SELECT
            current.tariff_code AS current_tariff_code,
            comparison.tariff_code AS comparison_tariff_code

        FROM
            octopus_agreements AS current

        JOIN
            octopus_agreements AS comparison
            ON comparison.mpan = current.mpan
            AND comparison.agreement_type = 'import'
            AND comparison.tariff_code != current.tariff_code

            AND comparison.valid_from < COALESCE(current.valid_to, '9999-12-31T23:59:59+00:00')

            AND (
                comparison.valid_to IS NULL
                OR comparison.valid_to > current.valid_from
            )

        WHERE
            current.agreement_type = 'import'

            AND current.valid_from <= ?

            AND (
                current.valid_to IS NULL
                OR current.valid_to > ?
            )

            AND current.product_code LIKE 'IOG-%'

        ORDER BY
            current.valid_from DESC,
            comparison.valid_from DESC

        LIMIT 1
        """

        row = conn.execute(
            query,
            (now, now),
        ).fetchone()

        conn.close()

        if row is None:
            raise RuntimeError("No comparison import tariff agreement found")

        return row["comparison_tariff_code"]

    def get_current_export_tariff(self) -> str:

        conn = get_connection()

        now = pd.Timestamp.now(tz="UTC").isoformat()

        query = """
        SELECT
            tariff_code
    
        FROM
            octopus_agreements
    
        WHERE
            agreement_type = 'export'
    
            AND valid_from <= ?
    
            AND (
                valid_to IS NULL
                OR valid_to > ?
            )
    
        ORDER BY
            valid_from DESC
    
        LIMIT 1
        """

        row = conn.execute(
            query,
            (now, now),
        ).fetchone()

        conn.close()

        if row is None:
            raise RuntimeError(
                "No current export tariff agreement found"
            )

        return row[0]

    def get_all_tariffs(self) -> pd.DataFrame:

        conn = get_connection()

        query = """
        SELECT *

        FROM octopus_tariffs

        ORDER BY
            tariff_code,
            valid_from
        """

        df = pd.read_sql_query(query, conn)

        conn.close()

        return df

    def get_four_rate_tariffs_for_period(
        self,
        tariff_code: str,
        period_start: datetime,
        period_end: datetime,
        include_vat: bool = True,
    ) -> list[dict]:
        """Load four-rate tariff periods relevant to an analysis period."""

        if period_start.tzinfo is None or period_end.tzinfo is None:
            raise ValueError("period_start and period_end must be timezone-aware")

        if period_end <= period_start:
            raise ValueError("period_end must be after period_start")

        start_iso = (
            period_start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        end_iso = period_end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        conn = get_connection()

        try:
            rows = conn.execute(
                """
                SELECT
                    id,
                    rate_type,
                    value_inc_vat,
                    value_exc_vat,
                    valid_from,
                    valid_to
                FROM octopus_four_rate_tariffs
                WHERE tariff_code = ?
                  AND valid_from < ?
                  AND (valid_to IS NULL OR valid_to > ?)
                ORDER BY valid_from DESC
                """,
                (
                    tariff_code,
                    end_iso,
                    start_iso,
                ),
            ).fetchall()

        finally:
            conn.close()

        return [
            {
                "tariff_id": row["id"],
                "rate_type": row["rate_type"],
                "rate_p_per_kwh": (
                    row["value_inc_vat"] if include_vat else row["value_exc_vat"]
                ),
                "valid_from": row["valid_from"],
                "valid_to": row["valid_to"],
            }
            for row in rows
        ]




    # ============================================
    # CONSUMPTION COSTS
    # ============================================

    def get_octopus_consumption_costs(
        self,
        period_from=None,
        period_to=None,
    ) -> pd.DataFrame:
        conn = get_connection()

        query = """
            SELECT
                interval_start,
                interval_end,
                consumption_kwh,
                tou_bucket,
                rate_p_per_kwh,
                cost_excl_vat_p,
                cost_incl_vat_p
            FROM octopus_consumption_costs
            WHERE 1 = 1
        """

        params = []

        if period_from is not None:
            query += " AND interval_start >= ?"
            params.append(period_from)

        if period_to is not None:
            query += " AND interval_start < ?"
            params.append(period_to)

        query += " ORDER BY interval_start"

        df = pd.read_sql_query(
            query,
            conn,
            params=params,
        )

        conn.close()

        if not df.empty:
            df["interval_start"] = pd.to_datetime(
                df["interval_start"]
            )

            df["interval_end"] = pd.to_datetime(
                df["interval_end"]
            )

        return df



        return df

    def upsert_consumption_costs(
        self,
        cost_df: pd.DataFrame,
    ) -> int:

        if cost_df.empty:
            return 0

        conn = get_connection()

        now = datetime.now().isoformat()
        rows_changed = 0

        for _, row in cost_df.iterrows():
            result = conn.execute(
                """
                INSERT INTO octopus_consumption_costs (
                    interval_start,
                    interval_end,
                    consumption_kwh,
                    tou_bucket,
                    rate_p_per_kwh,
                    cost_excl_vat_p,
                    cost_incl_vat_p,
                    first_seen,
                    last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(
                    interval_start,
                    interval_end
                )
                DO UPDATE SET

                    consumption_kwh =
                        excluded.consumption_kwh,

                    tou_bucket =
                        excluded.tou_bucket,

                    rate_p_per_kwh =
                        excluded.rate_p_per_kwh,

                    cost_excl_vat_p =
                        excluded.cost_excl_vat_p,

                    cost_incl_vat_p =
                        excluded.cost_incl_vat_p,

                    last_seen =
                        excluded.last_seen
                """,
                (
                    row["interval_start"].isoformat(),
                    row["interval_end"].isoformat(),
                    row["consumption_kwh"],
                    row["tou_bucket"],
                    row["rate_p_per_kwh"],
                    row["cost_excl_vat_p"],
                    row["cost_incl_vat_p"],
                    now,
                    now,
                ),
            )

            if result.rowcount:
                rows_changed += 1

        conn.commit()
        conn.close()

        return rows_changed

    def get_current_import_rate(self) -> float | None:
        conn = get_connection()

        now = pd.Timestamp.now(tz="Europe/London")
        current_time = now.time()

        if time(22, 30) <= current_time or current_time < time(4, 30):
            rate_type = "NIGHT"
        else:
            rate_type = "DAY"

        now_iso = now.isoformat().replace("+00:00", "Z")

        query = """
        SELECT value_inc_vat
        FROM octopus_four_rate_tariffs
        WHERE tariff_code = ?
          AND rate_type = ?
          AND valid_from <= ?
          AND (valid_to IS NULL OR valid_to > ?)
        ORDER BY valid_from DESC
        LIMIT 1
        """

        row = conn.execute(
            query,
            (
                self.get_current_import_tariff(),
                rate_type,
                now_iso,
                now_iso,
            ),
        ).fetchone()

        conn.close()

        if row is None:
            return None

        return row["value_inc_vat"]
    
    
    def get_current_export_rate(self) -> float | None:
        conn = get_connection()

        now = pd.Timestamp.now(tz="UTC").isoformat()

        query = """
        SELECT value_inc_vat
        FROM octopus_tariffs
        WHERE tariff_code = 'E-1R-OUTGOING-VAR-24-10-26-A'
          AND valid_from <= ?
          AND (valid_to IS NULL OR valid_to > ?)
        ORDER BY valid_from DESC
        LIMIT 1
        """

        row = conn.execute(query, (now, now)).fetchone()

        conn.close()

        if row is None:
            return None

        return row["value_inc_vat"]




