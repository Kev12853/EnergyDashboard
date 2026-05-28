from datetime import datetime

from services.db import (
    get_connection,
)

from services.octopus.api.octopus_api import (
    get_octopus_agreements,
)

from services.config import (
    IMPORT_MPAN,
    EXPORT_MPAN,
)


def save_agreements():

    conn = get_connection()

    agreements = (
        get_octopus_agreements()
    )

    created_at = (
        datetime.now()
        .isoformat()
    )

    rows_added = 0

    for agreement in agreements:

        mpan = (
            agreement["mpan"]
        )

        if mpan == IMPORT_MPAN:

            agreement_type = (
                "import"
            )

        elif mpan == EXPORT_MPAN:

            agreement_type = (
                "export"
            )

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

                agreement[
                    "account_number"
                ],

                mpan,

                agreement_type,

                agreement[
                    "tariff_type"
                ],

                agreement[
                    "product_code"
                ],

                agreement[
                    "tariff_code"
                ],

                agreement[
                    "valid_from"
                ],

                agreement[
                    "valid_to"
                ],

                created_at,

            ),
        )

        if result.rowcount:

            rows_added += 1

    print("\nAGREEMENTS TABLE\n")


    conn.commit()

    conn.close()

    print(
        f"Agreements added: "
        f"{rows_added}"
    )


if __name__ == "__main__":

    save_agreements()