import json

import requests

from services.config import (
    API_KEY,
    GRAPHQL_URL,
)


# =====================================================
# GET GRAPHQL TOKEN
# =====================================================

token_query = f"""
mutation {{

  obtainKrakenToken(
    input: {{
      APIKey: "{API_KEY}"
    }}
  ) {{

    token

  }}
}}
"""

response = requests.post(
    GRAPHQL_URL,
    json={
        "query": token_query
    },
    headers={
        "Content-Type":
            "application/json"
    },
    timeout=10,
)

response.raise_for_status()

token = (
    response.json()
    ["data"]
    ["obtainKrakenToken"]
    ["token"]
)

print("\nTOKEN OK\n")


# =====================================================
# TEST 1
# ACCOUNT QUERY INTROSPECTION
# =====================================================

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

            ... on FourRateEvTariff {

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
    json={
        "query": query
    },
    headers={
        "Authorization": token,
        "Content-Type":
            "application/json",
    },
    timeout=10,
)

print("\nSTATUS CODE\n")

print(response.status_code)

print("\nRESPONSE\n")

print(
    json.dumps(
        response.json(),
        indent=2,
    )
)

# print("\nVIEWER DATA\n")
#
# print(
#     json.dumps(
#         data,
#         indent=2,
#     )
# )


# =====================================================
# TEST 2
# TRY FLEX QUERY
# =====================================================
#?