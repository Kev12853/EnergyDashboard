import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_secret(key):
    return st.secrets.get(
        key,
        os.getenv(key)
    )


API_KEY = get_secret("OCTOPUS_API_KEY")
ACCOUNT_ID = get_secret("ACCOUNT_ID")

IMPORT_MPAN = get_secret("IMPORT_MPAN")
EXPORT_MPAN = get_secret("EXPORT_MPAN")

METER_SERIAL = get_secret("METER_SERIAL")

PRODUCT_CODE = get_secret("PRODUCT_CODE")
TARIFF_CODE = get_secret("TARIFF_CODE")

BASE_URL = "https://api.octopus.energy/v1"
GRAPHQL_URL = "https://api.octopus.energy/v1/graphql/"

TIMEZONE = "Europe/London"