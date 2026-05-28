from datetime import datetime

from services.db import (
    get_connection,
)
from services.octopus.api.octopus_api import (
    get_octopus_accounts,
)


def save_accounts():

    conn = get_connection()

    accounts = get_octopus_accounts()

    created_at = (
        datetime.now()
        .isoformat()
    )

    rows_added = 0

    for account in accounts:

        account_number = (
            account["number"]
        )

        result = conn.execute(
            """
            INSERT OR IGNORE INTO
            octopus_accounts (

                account_number,

                created_at

            )

            VALUES (?, ?)
            """,
            (
                account_number,
                created_at,
            ),
        )

        if result.rowcount:

            rows_added += 1

    conn.commit()

    conn.close()

    print(
        f"Accounts added: "
        f"{rows_added}"
    )


if __name__ == "__main__":

    save_accounts()