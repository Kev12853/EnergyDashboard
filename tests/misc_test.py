from app.connections.connection import get_connection

connection = get_connection()

rows = connection.execute(
    """
    SELECT
        id,
        tariff_code,
        value_inc_vat,
        valid_from,
        valid_to,
        created_at
    FROM octopus_tariffs
    WHERE tariff_code = 'E-1R-INTELLI-FIX-12M-26-04-18-A'
    ORDER BY valid_from
    """
).fetchall()

for row in rows:
    print(dict(row))

connection.close()