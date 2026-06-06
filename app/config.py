import os

from dotenv import load_dotenv


# =====================================================
# LOAD ENVIRONMENT VARIABLES
# =====================================================

load_dotenv()


# =====================================================
# OCTOPUS CONFIG
# =====================================================

API_KEY = os.getenv("OCTOPUS_API_KEY")

ACCOUNT_ID = os.getenv("ACCOUNT_ID")

IMPORT_MPAN = os.getenv("IMPORT_MPAN")

EXPORT_MPAN = os.getenv("EXPORT_MPAN")

METER_SERIAL = os.getenv("METER_SERIAL")

PRODUCT_CODE = os.getenv("PRODUCT_CODE")

TARIFF_CODE = os.getenv("TARIFF_CODE")


# =====================================================
# URLS
# =====================================================

BASE_URL = "https://api.octopus.energy/v1"

GRAPHQL_URL = "https://api.octopus.energy/v1/graphql/"


# =====================================================
# TIMEZONE
# =====================================================

TIMEZONE = "Europe/London"
