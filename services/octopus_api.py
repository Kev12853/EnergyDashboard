import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# -----------------------
# CONFIG
# -----------------------
API_KEY = os.getenv("OCTOPUS_API_KEY")
ACCOUNT_ID = os.getenv("OCTOPUS_ACCOUNT_NUMBER")

IMPORT_MPAN = os.getenv("IMPORT_MPAN")
EXPORT_MPAN = os.getenv("EXPORT_MPAN")

SERIAL = os.getenv("METER_SERIAL")

PRODUCT_CODE = os.getenv("PRODUCT_CODE")
TARIFF_CODE = os.getenv("TARIFF_CODE")

BASE_URL = "https://api.octopus.energy"
TIMEZONE = "Europe/London"


# -----------------------
# HELPERS
# -----------------------

@st.cache_data(ttl=300)
def get_graphql_token():

    url = f"{BASE_URL}/v1/graphql/"

    query = """
    mutation {
      obtainKrakenToken(input: {
        APIKey: "%s"
      }) {
        token
      }
    }
    """ % API_KEY

    response = requests.post(
        url,
        json={"query": query},
        headers={
            "Content-Type": "application/json"
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    errors = data.get("errors")

    if errors:
        raise Exception(errors)

    return (
        data["data"]
        ["obtainKrakenToken"]
        ["token"]
    )

def to_local_time(series):
    return (
        pd.to_datetime(series, utc=True)
        .dt.tz_convert(TIMEZONE)
        .dt.tz_localize(None)
    )


def fetch_all_pages(url, params):
    results = []

    while url:
        try:
            response = requests.get(
                url,
                params=params,
                auth=(API_KEY, ""),
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            results.extend(data.get("results", []))

            url = data.get("next")
            params = None

        except requests.HTTPError as e:
            st.error(f"Octopus API Error: {e}")
            return []

        except Exception as e:
            st.error(f"Connection Error: {e}")
            return []

    return results


def get_meter_data(mpan, column_name, period_from=None, period_to=None):
    url = (
        f"{BASE_URL}/v1/electricity-meter-points/"
        f"{mpan}/meters/{SERIAL}/consumption/"
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


# -----------------------
# TARIFFS
# -----------------------
@st.cache_data(ttl=1800)
def get_tariffs(period_from=None, period_to=None):

    url = (
        f"{BASE_URL}/v1/products/{PRODUCT_CODE}/"
        f"electricity-tariffs/{TARIFF_CODE}/"
        f"standard-unit-rates/"
    )

    params = {"page_size": 25000}

    if period_from:
        params["period_from"] = period_from

    if period_to:
        params["period_to"] = period_to

    data = fetch_all_pages(url, params)

    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["datetime", "unit_rate"])

    df["datetime"] = to_local_time(df["valid_from"])

    # Convert pence → pounds
    df["unit_rate"] = df["value_inc_vat"] / 100

    return df[["datetime", "unit_rate"]].sort_values("datetime")


# -----------------------
# CONSUMPTION + EXPORT
# -----------------------
@st.cache_data(ttl=1800)
def get_consumption(period_from=None, period_to=None):

    df_import = get_meter_data(
        IMPORT_MPAN,
        "consumption_kwh",
        period_from,
        period_to
    )

    if df_import.empty:
        return pd.DataFrame(
            columns=[
                "datetime",
                "consumption_kwh",
                "export_kwh"
            ]
        )

    df_export = get_meter_data(
        EXPORT_MPAN,
        "export_kwh",
        period_from,
        period_to
    )

    df = pd.merge(
        df_import,
        df_export,
        on="datetime",
        how="left"
    )

    df["export_kwh"] = df["export_kwh"].fillna(0)

    return df.sort_values("datetime")


# -----------------------
# INTELLIGENT DISPATCHES
# -----------------------
@st.cache_data(ttl=300)
def get_intelligent_dispatches():

    url = "https://api.octopus.energy/v1/graphql/"

    query = """
    query getDispatches($accountNumber: String!) {

        plannedDispatches(accountNumber: $accountNumber) {
            startDt
            endDt
            deltaKwh
        }

        completedDispatches(accountNumber: $accountNumber) {
            startDt
            endDt
            deltaKwh
        }
    }
    """

    try:
        token = get_graphql_token()

        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }

        response = requests.post(
            url,
            json={
                "query": query,
                "variables": {
                    "accountNumber": ACCOUNT_ID
                }
            },
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json().get("data", {})

        planned = pd.DataFrame(
            data.get("plannedDispatches") or []
        )

        completed = pd.DataFrame(
            data.get("completedDispatches") or []
        )

        if not planned.empty:
            planned["status"] = "Planned"

        if not completed.empty:
            completed["status"] = "Completed"

        df = pd.concat(
            [planned, completed],
            ignore_index=True
        )

        if not df.empty:

            df["startDt"] = to_local_time(df["startDt"])

            df["endDt"] = to_local_time(df["endDt"])

        return df

    except Exception as e:
        st.error(f"Dispatch API Error: {e}")
        return pd.DataFrame()