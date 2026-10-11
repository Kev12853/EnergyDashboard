from app.octopus.api.octopus_api import get_tariffs

tariffs = get_tariffs(
    "E-1R-IOG-SMB-FIX-12M-26-04-18-A",
    period_from="2026-08-31T23:00:00Z",
    period_to="2026-09-02T00:00:00Z",
)

print(f"Returned {len(tariffs)} tariff periods")

for tariff in tariffs:
    print(tariff)