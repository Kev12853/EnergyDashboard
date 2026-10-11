import json

import pandas as pd
import requests

# import streamlit as st
from pandas import DataFrame

from app.config.octopus_config import (
    ACCOUNT_ID,
    BASE_URL,
    EXPORT_MPAN,
    GRAPHQL_URL,
    IMPORT_MPAN,
    METER_SERIAL,
    OCTOPUS_API_KEY,
    TIMEZONE,
)
from app.connections.connection import get_connection
from app.octopus.costs.octopus_cost_analysis import (
    calculate_octopus_actual_costs,
    summarise_octopus_actual_costs,
    calculate_smart_flex_savings,
    summarise_smart_flex_savings,
)
from app.octopus.costs.octopus_tariff_matching import get_tariff_for_period


# -----------------------
# CONFIG
# -----------------------
# def get_secret(key):
#     return st.secrets.get(
#         key,
#         os.getenv(key)
#     )
#
#
# OCTOPUS_API_KEY = get_secret("OCTOPUS_API_KEY")
# IMPORT_MPAN = get_secret("IMPORT_MPAN")
# EXPORT_MPAN = get_secret("EXPORT_MPAN")
# METER_SERIAL = get_secret("METER_SERIAL")
# PRODUCT_CODE = get_secret("PRODUCT_CODE")
# TARIFF_CODE = get_secret("TARIFF_CODE")
# ACCOUNT_ID = get_secret("ACCOUNT_ID")
#
# BASE_URL = "https://api.octopus.energy/v1"
# GRAPHQL_URL = "https://api.octopus.energy/v1/graphql/"
# TIMEZONE = "Europe/London"

# -----------------------
# HELPERS
# -----------------------


def get_graphql_token():

    url = GRAPHQL_URL

    query = (
        """
    mutation {
      obtainKrakenToken(input: {
        APIKey: "%s"
      }) {
        token
      }
    }
    """
        % OCTOPUS_API_KEY
    )

    response = requests.post(
        url,
        json={"query": query},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    errors = data.get("errors")

    if errors:
        raise Exception(errors)

    return data["data"]["obtainKrakenToken"]["token"]


def to_local_time(series):
    return pd.to_datetime(series, utc=True).dt.tz_convert(TIMEZONE).dt.tz_localize(None)


def fetch_all_pages(url, params):
    results = []

    while url:
        try:
            response = requests.get(
                url, params=params, auth=(OCTOPUS_API_KEY, ""), timeout=10
            )

            response.raise_for_status()

            data = response.json()

            results.extend(data.get("results", []))

            url = data.get("next")
            params = None

        except requests.HTTPError as e:
            raise RuntimeError(f"Octopus API Error: {e}") from e

        except Exception as e:
            raise RuntimeError(f"Connection Error: {e}") from e

    return results


def get_meter_data(mpan, column_name, period_from=None, period_to=None):
    url = (
        f"{BASE_URL}/electricity-meter-points/{mpan}/meters/{METER_SERIAL}/consumption/"
    )

    params = {"page_size": 25000}

    if period_from:
        params["period_from"] = period_from

    if period_to:
        params["period_to"] = period_to

    data = fetch_all_pages(url, params)

    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["datetime", column_name])

    df["datetime"] = to_local_time(df["interval_start"])

    df[column_name] = df["consumption"]

    return df[["datetime", column_name]].sort_values("datetime")


def get_tariffs(
    tariff_code,
    period_from=None,
    period_to=None,
):
    parts = tariff_code.split("-")

    product_code = "-".join(parts[2:-1])

    url = (
        f"{BASE_URL}"
        f"/products/"
        f"{product_code}/"
        f"electricity-tariffs/"
        f"{tariff_code}/"
        f"standard-unit-rates/"
    )

    params = {"page_size": 25000}

    if period_from:
        params["period_from"] = period_from

    if period_to:
        params["period_to"] = period_to

    # print("TARIFF URL:", url)
    # print("TARIFF PARAMS:", params)

    data = fetch_all_pages(
        url,
        params,
    )

    # print("TARIFF RAW ROW COUNT:", len(data))
    # print("TARIFF RAW DATA:", data[:3])

    return pd.DataFrame(data)


def get_four_rate_tariffs(
    tariff_code,
    period_from=None,
    period_to=None,
):
    parts = tariff_code.split("-")

    product_code = "-".join(parts[2:-1])

    base_url = (
        f"{BASE_URL}"
        f"/products/"
        f"{product_code}/"
        f"electricity-tariffs/"
        f"{tariff_code}/"
    )

    rate_endpoints = {
        "DAY": "day-unit-rates/",
        "NIGHT": "night-unit-rates/",
        "EV_DEVICE_PEAK": "ev-device-peak-unit-rates/",
        "EV_DEVICE_OFF_PEAK": "ev-device-off-peak-unit-rates/",
    }

    rows = []

    for rate_type, endpoint in rate_endpoints.items():

        url = base_url + endpoint

        params = {"page_size": 25000}

        if period_from:
            params["period_from"] = period_from

        if period_to:
            params["period_to"] = period_to

        data = fetch_all_pages(
            url,
            params,
        )

        for row in data:
            row = row.copy()
            row["rate_type"] = rate_type
            rows.append(row)

    return pd.DataFrame(rows)

SMARTFLEX_VEHICLE_ID = "00000000-0002-4000-8020-000000100c8e"

CAR_CONNECTED_STATES = {
    "SMART_CONTROL_CAPABLE",
    "SMART_CONTROL_IN_PROGRESS",
}


def get_smartflex_vehicle_status() -> dict | None:
    """
    Returns the current Smart Flex status of the registered vehicle.
    """

    query = """
    query GetSmartFlexVehicleStatus(
        $accountNumber: String!
        $deviceId: String!
    ) {
        devices(
            accountNumber: $accountNumber
            deviceId: $deviceId
        ) {
            __typename
            id
            name
            status {
                __typename
                ... on SmartFlexVehicleStatus {
                    current
                    isSuspended
                    currentState
                    stateOfCharge {
                        value
                    }
                    activePower {
                        value
                    }
                }
            }
        }
    }
    """

    token = get_graphql_token()

    response = requests.post(
        GRAPHQL_URL,
        json={
            "query": query,
            "variables": {
                "accountNumber": ACCOUNT_ID,
                "deviceId": SMARTFLEX_VEHICLE_ID,
            },
        },
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
        },
        timeout=10,
    )

    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    devices = data["data"]["devices"]

    if not devices:
        return None

    device = devices[0]
    status = device.get("status")

    if not status:
        return None

    current_state = status.get("currentState")

    return {
        "vehicle": device.get("name"),
        "state": current_state,
        "lifecycle": status.get("current"),
        "suspended": status.get("isSuspended", False),
        "connected": current_state in CAR_CONNECTED_STATES,
        "soc": float(status["stateOfCharge"]["value"]),
        "active_power_kw": float(status["activePower"]["value"]),
        "charging": float(status["activePower"]["value"]) > 0,
    }


# -----------------------
# CONSUMPTION + EXPORT
# -----------------------
def get_consumption(period_from=None, period_to=None):

    df_import = get_meter_data(IMPORT_MPAN, "consumption_kwh", period_from, period_to)

    if df_import.empty:
        return pd.DataFrame(columns=["datetime", "consumption_kwh", "export_kwh"])

    df_export = get_meter_data(EXPORT_MPAN, "export_kwh", period_from, period_to)

    df = pd.merge(df_import, df_export, on="datetime", how="left")

    df["export_kwh"] = df["export_kwh"].fillna(0)

    return df.sort_values("datetime")


def get_octopus_accounts():

    token = get_graphql_token()

    query = """
    query {

      viewer {

        accounts {

          number

        }

      }

    }
    """

    response = requests.post(
        GRAPHQL_URL,
        json={"query": query},
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
        },
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()["data"]["viewer"]["accounts"]

    return data


def get_octopus_agreements():

    token = get_graphql_token()

    query = """
    query {

      viewer {

        accounts {

          number

          ... on AccountType {

            electricityAgreements {

              validFrom

              validTo

              meterPoint {

                mpan

              }

              tariff {

                __typename

                ... on TariffType {

                  productCode

                  tariffCode

                }

                ... on HalfHourlyTariff {

                  productCode

                  tariffCode

                }

                ... on DayNightTariff {

                  productCode

                  tariffCode

                }

                ... on StandardTariff {

                  productCode

                  tariffCode

                }

              }

            }

          }

        }

      }

    }
    """

    response = requests.post(
        GRAPHQL_URL,
        json={"query": query},
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
        },
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()["data"]["viewer"]["accounts"]

    results = []

    for account in data:
        for agreement in account["electricityAgreements"]:
            tariff = agreement["tariff"]

            results.append(
                {
                    "account_number": account["number"],
                    "mpan": agreement["meterPoint"]["mpan"],
                    "valid_from": agreement["validFrom"],
                    "valid_to": agreement["validTo"],
                    "tariff_type": tariff["__typename"],
                    "product_code": tariff["productCode"],
                    "tariff_code": tariff["tariffCode"],
                }
            )

    return results


# -----------------------
# INTELLIGENT DISPATCHES
# -----------------------

def get_intelligent_dispatches() -> pd.DataFrame:
    """
    Retrieves the current Intelligent Octopus Smart Flex dispatch plan.

    Returns a DataFrame with the standard application schema:

        dispatch_start
        dispatch_end
        scheduled_energy_kwh
        status
    """
    SMARTFLEX_VEHICLE_ID = "00000000-0002-4000-8020-000000100c8e"

    query = """
    query getDispatches($deviceId: String!) {

        flexPlannedDispatches(deviceId: $deviceId) {
            start
            end
            energyAddedKwh
            type
        }
    }
    """

    try:
        token = get_graphql_token()

        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }

        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": query,
                "variables": {
                    "deviceId": SMARTFLEX_VEHICLE_ID,
                },
            },
            headers=headers,
            timeout=10,
        )

        if not response.ok:
            # print("DISPATCH API STATUS:", response.status_code)
            # print("DISPATCH API RESPONSE:", response.text)
            response.raise_for_status()

        data = response.json().get("data", {})

        df = pd.DataFrame(data.get("flexPlannedDispatches") or [])

        if df.empty:
            return df

        df["status"] = "Planned"

        # Convert to local timezone
        df["start"] = to_local_time(df["start"])
        df["end"] = to_local_time(df["end"])

        # Rename to application field names
        df = df.rename(
            columns={
                "start": "dispatch_start",
                "end": "dispatch_end",
                "energyAddedKwh": "scheduled_energy_kwh",
            }
        )

        # Ensure numeric type
        df["scheduled_energy_kwh"] = pd.to_numeric(
            df["scheduled_energy_kwh"],
            errors="coerce",
        )

        # Return in a consistent column order
        return df[
            [
                "dispatch_start",
                "dispatch_end",
                "scheduled_energy_kwh",
                "status",
            ]
        ]

    except Exception as e:
        raise RuntimeError(f"Dispatch API Error: {e}") from e


def get_completed_dispatches() -> pd.DataFrame:
    """
    Retrieves recently completed Intelligent Octopus Smart Flex dispatches.

    Returns a DataFrame with the standard application schema:

        dispatch_start
        dispatch_end
        scheduled_energy_kwh
        status
    """

    query = """
    query($accountNumber: String!) {
        completedDispatches(accountNumber: $accountNumber) {
            start
            end
        }
    }
    """

    try:
        token = get_graphql_token()

        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }

        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": query,
                "variables": {
                    "accountNumber": ACCOUNT_ID,
                },
            },
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

        result = response.json()

        errors = result.get("errors")
        if errors:
            raise RuntimeError(errors)

        data = result.get("data", {})

        df = pd.DataFrame(
            data.get("completedDispatches") or []
        )

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "dispatch_start",
                    "dispatch_end",
                    "scheduled_energy_kwh",
                    "status",
                ]
            )

        df["status"] = "Completed"

        # Convert to local timezone
        df["start"] = to_local_time(df["start"])
        df["end"] = to_local_time(df["end"])

        # Rename to application field names
        df = df.rename(
            columns={
                "start": "dispatch_start",
                "end": "dispatch_end",
            }
        )

        # Completed dispatches do not provide the same
        # energy value as the planned dispatch API.
        df["scheduled_energy_kwh"] = 0.0

        # Return in a consistent column order
        return df[
            [
                "dispatch_start",
                "dispatch_end",
                "scheduled_energy_kwh",
                "status",
            ]
        ]

    except Exception as e:
        raise RuntimeError(
            f"Completed Dispatch API Error: {e}"
        ) from e


# -----------------------
# DEVICE CONSUMPTION BREAKDOWN
# -----------------------
def get_device_consumption_breakdown(
    start_at: str,
    end_at: str,
) -> pd.DataFrame:

    query = """
    query getDeviceConsumptionBreakdown(
        $accountNumber: String!
        $first: Int!
        $utilityFilters: [UtilityFiltersInput!]
        $startAt: DateTime
        $endAt: DateTime
        $timezone: String
        $cursor: String
    ) {
        account(accountNumber: $accountNumber) {
            properties {
                measurements(
                    first: $first
                    utilityFilters: $utilityFilters
                    startAt: $startAt
                    endAt: $endAt
                    timezone: $timezone
                    after: $cursor
                ) {
                    edges {
                        node {
                            value
                            unit

                            ... on IntervalMeasurementType {
                                startAt
                                endAt
                                durationInSeconds
                            }

                            metaData {
                                statistics {
                                    costExclTax {
                                        pricePerUnit {
                                            amount
                                        }
                                        costCurrency
                                        estimatedAmount
                                    }

                                    costInclTax {
                                        pricePerUnit {
                                            amount
                                        }
                                        costCurrency
                                        estimatedAmount
                                    }

                                    value
                                    description
                                    label
                                    type
                                }
                            }
                        }
                    }

                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        }
    }
    """

    variables = {
        "accountNumber": ACCOUNT_ID,
        "first": 100,
        "utilityFilters": [
            {
                "electricityFilters": {
                    "readingFrequencyType": "RAW_INTERVAL",
                    "readingDirection": "CONSUMPTION",
                    "marketSupplyPointId": IMPORT_MPAN,
                }
            }
        ],
        "startAt": start_at,
        "endAt": end_at,
        "timezone": TIMEZONE,
        "cursor": None,
    }

    token = get_graphql_token()

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }

    rows = []

    while True:
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": query,
                "variables": variables,
            },
            headers=headers,
        )

        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            raise RuntimeError(data["errors"])

        measurements = data["data"]["account"]["properties"][0]["measurements"]

        # print(
        #     "OCTOPUS MEASUREMENT EDGES:",
        #     len(measurements["edges"]),
        # )
        # print(
        #     "OCTOPUS PAGE INFO:",
        #     measurements["pageInfo"],
        # )

        diagnostic_rows = []

        for edge in measurements["edges"]:
            node = edge["node"]

            statistics = node.get("metaData", {}).get("statistics", [])

            # ------------------------------------------------
            # Temporary tariff diagnostic
            # Print the first 10 intervals returned by
            # Octopus, showing the rate components.
            # ------------------------------------------------

            if len(diagnostic_rows) < 10:
                rate_components = [
                    {
                        "label": stat.get("label"),
                        "value": stat.get("value"),
                        "rate": (
                            stat.get("costExclTax", {})
                            .get("pricePerUnit", {})
                            .get("amount")
                            if stat.get("costExclTax", {}).get("pricePerUnit")
                            else None
                        ),
                    }
                    for stat in statistics
                    if stat.get("type") == "CONSUMPTION_COST"
                ]

                # print(
                #     "OCTOPUS RATE DIAGNOSTIC:",
                #     node.get("startAt"),
                #     node.get("endAt"),
                #     "consumption=",
                #     node.get("value"),
                #     rate_components,
                # )

                diagnostic_rows.append(node)

            # ------------------------------------------------
            # Existing processing continues here
            # ------------------------------------------------

            # Your existing consumption_stats / tou_stats
            # and rows.append(...) code goes here.

        page_info = measurements["pageInfo"]

        if not page_info["hasNextPage"]:
            break

        variables["cursor"] = page_info["endCursor"]

    if not rows:
        return pd.DataFrame(
            columns=[
                "interval_start",
                "interval_end",
                "consumption_kwh",
                "tou_bucket",
                "rate_p_per_kwh",
                "cost_excl_vat_p",
                "cost_incl_vat_p",
            ]
        )

    df = pd.DataFrame(rows)

    df["interval_start"] = to_local_time(
        df["interval_start"]
    )

    df["interval_end"] = to_local_time(
        df["interval_end"]
    )

    return df


#
# if __name__ == "__main__":
#     from app.octopus.storage.repository import OctopusRepository
#
#     repository = OctopusRepository()
#
#     # -------------------------------------------------
#     # Test API → database
#     # -------------------------------------------------
#
#     df = get_device_consumption_breakdown(
#         "2026-08-04T23:00:00.000Z",
#         "2026-08-05T23:00:00.000Z",
#     )
#
#     print(df.to_string(index=False))
#
#     rows_changed = repository.upsert_consumption_costs(df)
#
#     print()
#     print(f"Rows changed: {rows_changed}")
#
#     # -------------------------------------------------
#     # Test database → DataFrame
#     # -------------------------------------------------
#
#     stored_df = repository.get_octopus_consumption_costs(
#         period_from="2026-08-05T00:00:00",
#         period_to="2026-08-06T00:00:00",
#     )
#
#     print()
#     print("Stored consumption costs:")
#     print(stored_df.to_string(index=False))
#
#     print()
#     print(f"Rows retrieved: {len(stored_df)}")
#
#     # -------------------------------------------------
#     # Test actual cost analysis
#     # -------------------------------------------------
#
#     actual_costs = calculate_octopus_actual_costs(
#         stored_df
#     )
#
#     print()
#     print("Actual cost analysis:")
#     print(actual_costs.to_string(index=False))
#
#     # -------------------------------------------------
#     # Test actual cost summary
#     # -------------------------------------------------
#
#     summary = summarise_octopus_actual_costs(
#         actual_costs
#     )
#
#     print()
#     print("Actual cost summary:")
#
#     for key, value in summary.items():
#         print(f"{key}: {value}")
#
#     # -------------------------------------------------
#     # Test Smart Flex savings
#     # -------------------------------------------------
#
#     savings = calculate_smart_flex_savings(
#         actual_costs,
#         "E-1R-INTELLI-FIX-12M-26-04-18-A",
#     )
#
#     print()
#     print("Smart Flex savings:")
#     print(savings.to_string(index=False))
#
#     summary = summarise_smart_flex_savings(savings)
#
#     print()
#     print("Smart Flex savings summary:")
#     for key, value in summary.items():
#         print(f"{key}: {value}")
#
#     conn = get_connection()
#
#     rows = conn.execute(
#         """
#         SELECT
#             id,
#             tariff_code,
#             value_exc_vat,
#             value_inc_vat,
#             valid_from,
#             valid_to
#         FROM octopus_tariffs
#         WHERE
#             tariff_code = ?
#             AND valid_from < ?
#             AND (
#                 valid_to IS NULL
#                 OR valid_to > ?
#             )
#         ORDER BY valid_from
#         """,
#         (
#             "E-1R-INTELLI-FIX-12M-26-04-18-A",
#             "2026-08-06T00:00:00Z",
#             "2026-08-05T00:00:00Z",
#         ),
#     ).fetchall()
#
#     print("\nDIRECT OCTOPUS TARIFF API TEST:")
#
#     tariffs = get_tariffs(
#         "E-1R-INTELLI-FIX-12M-26-04-18-A",
#         period_from="2026-08-04T23:00:00Z",
#         period_to="2026-08-05T23:00:00Z",
#     )
#
#     print(tariffs.to_string(index=False))
#
#     print()
#     print("Tariff records covering 5 August:")
#     for row in rows:
#         print(dict(row))
#
#     conn.close()
#
#     tariff = get_tariff_for_period(
#         tariff_code="E-1R-INTELLI-FIX-12M-26-04-18-A",
#         period_start=pd.Timestamp(
#             "2026-08-05T14:00:00", tz="Europe/London"
#         ).to_pydatetime(),
#         include_vat=False,
#     )
#
#     print()
#     print("Test tariff lookup:")
#     print(tariff)