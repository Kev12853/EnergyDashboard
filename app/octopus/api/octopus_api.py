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

    data = fetch_all_pages(
        url,
        params,
    )

    return pd.DataFrame(data)


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
