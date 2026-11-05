"""Overview page for the NiceGUI Energy Dashboard.

This page combines three main areas:
    - Live energy telemetry (PV, house consumption, battery, state of charge and grid).
    - A live energy-cost estimate based on current grid power and tariff rates.
    - Octopus Smart Flex cost summaries and a daily comparison chart.

The page reads telemetry through ``TelemetryRepository`` and tariff/cost data
through ``OctopusRepository`` and the Octopus cost-analysis helpers. It builds
its UI when ``render()`` is called by ``DashboardShell`` and refreshes live
telemetry every 30 seconds and cost summaries every 300 seconds.

Important assumptions reflected in the existing implementation:
    - Grid power below zero represents import; above zero represents export.
    - Battery power below zero represents discharge; above zero represents charge.
    - The daily live cost calculation uses one-minute telemetry history and matches
      each interval to an import or export tariff.
    - The live telemetry display reads the latest snapshot returned by the
      repository. Source labelling depends on the repository returning a
      ``telemetry_source`` field for cloud readings.

This documentation pass is intended to explain the existing code, not change its
behaviour. Debug print statements and commented-out code are preserved so they
can be reviewed separately during the project audit.
"""

from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

import pandas as pd
from nicegui import ui

from app.config.octopus_config import TIMEZONE
# Database connection and repository interfaces for Octopus and SolaX data.
from app.connections.connection import get_connection
from app.octopus.costs.octopus_cost_analysis import (
    get_smart_flex_summary,
    calculate_octopus_actual_costs,
    summarise_octopus_actual_costs,
)
from app.octopus.storage.repository import OctopusRepository
from app.solax.storage.solax_repository import TelemetryRepository
from app.energy.costs.energy_cost_service import EnergyCostService


class OverviewPage:
    """Build the Overview screen and refresh its telemetry and cost figures."""

    def __init__(self) -> None:
        """Initialise repositories, default date range and UI element references.

        The default reporting period is the most recent seven calendar dates,
        including today. UI references are initially ``None`` and are assigned
        when ``_create_octopus_section()`` builds the page.
        """
        self.octopus_repo = OctopusRepository()

        today = date.today()
        self.start_date = today - timedelta(days=6)
        self.end_date = today

        # UI element references populated during render().
        self.from_picker = None
        self.to_picker = None

        self.imported_label = None
        self.actual_cost_label = None
        self.normal_cost_label = None
        self.saving_label = None
        self.saving_percentage_label = None

        self.battery_label = None
        self.battery_status_label = None

        self.grid_label = None
        self.grid_status_label = None

        self.soc_label = None
        self.pv_label = None
        self.house_label = None
        self.telemetry_source_label = None

        self.energy_cost_value_label = None
        self.energy_cost_rate_label = None
        self.energy_cost_energy_import_label = None
        self.energy_cost_energy_export_label = None
        self.energy_cost_energy_net_label = None

        self.energy_cost_import_cost_label = None
        self.energy_cost_export_earnings_label = None
        self.energy_cost_net_cost_label = None

        self.cost_chart = None

        # Keep the connection and repository used for telemetry queries.
        # Connection lifetime/cleanup is managed outside this page in the
        # current implementation.
        self.connection = get_connection()
        self.telemetry_repo = TelemetryRepository(self.connection)
        self.energy_cost_service = EnergyCostService(self.telemetry_repo)

    def render(self, shell) -> None:
        """Render the page and start its periodic refresh callbacks.

        Args:
            shell: The DashboardShell instance hosting this page. It is retained
                on the instance for potential page-level access to shell state.
        """
        self.shell = shell
        ui.label("Overview").classes("text-h5")

        # Build the cards and chart before refreshing their displayed values.
        self._create_octopus_section()
        self.refresh_live_energy()
        self.refresh()

        # Refresh high-frequency telemetry more often than historical cost data.
        ui.timer(30, self.refresh_live_energy)
        ui.timer(300, self.refresh)

    def _create_octopus_section(self) -> None:
        """Create the live energy cards, Octopus summary controls and chart.

        Despite the method name, this builds both the live SolaX energy section
        and the Octopus cost-analysis section.
        """
        # Live telemetry cards.
        with ui.card().classes("w-full"):
            ui.label("Current Energy Status").classes("text-h6")
            self.telemetry_source_label = ui.label("Source: —").classes(
                "text-caption text-grey"
            )

            with ui.row().classes("w-full gap-4 wrap"):
                with ui.card().classes("flex-1"):
                    ui.label("PV").classes("text-caption")
                    self.pv_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("House").classes("text-caption")
                    self.house_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("SOC").classes("text-caption")
                    self.soc_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("Battery").classes("text-caption")
                    self.battery_label = ui.label("—").classes("text-h6")
                    self.battery_status_label = ui.label("").classes("text-subtitle2")

                with ui.card().classes("flex-1"):
                    ui.label("Grid").classes("text-caption")
                    self.grid_label = ui.label("—").classes("text-h6")
                    self.grid_status_label = ui.label("").classes("text-subtitle2")

        # Live estimate based on the current grid reading and current rates.
        with ui.card().classes("w-full"):
            ui.label("Energy Cost").classes("text-h6")

            with ui.row().classes("w-full gap-4 wrap"):
                with ui.card().classes("flex-1"):
                    ui.label("Current").classes("text-caption")
                    self.energy_cost_value_label = ui.label("—").classes(
                        "text-subtitle1"
                    )

                with ui.card().classes("flex-1"):
                    ui.label("Rate").classes("text-caption")
                    self.energy_cost_rate_label = ui.label("—").classes(
                        "text-body2 whitespace-pre-line"
                    )

                with ui.card().classes("flex-1"):
                    ui.label("Energy Today").classes("text-caption")

                    with ui.row().classes("w-full gap-8"):
                        with ui.column().classes("flex-1 gap-1"):
                            self.energy_cost_energy_import_label = ui.label("Import: —")
                        with ui.column().classes("flex-1 gap-1"):
                            self.energy_cost_energy_export_label = ui.label("Export: —")

                    self.energy_cost_energy_net_label = ui.label("Net: —")

                with ui.card().classes("flex-1"):
                    ui.label("Today (£)").classes("text-caption")

                    with ui.row().classes("w-full gap-8"):
                        with ui.column().classes("flex-1 gap-1"):
                            self.energy_cost_import_cost_label = ui.label("Import: —")
                        with ui.column().classes("flex-1 gap-1"):
                            self.energy_cost_export_earnings_label = ui.label(
                                "Export: —"
                            )

                    self.energy_cost_net_cost_label = ui.label("Net: —")

        # Historical Octopus summary controls, totals and daily chart.
        with ui.card().classes("w-full"):
            ui.label("Octopus Energy").classes("text-h6")

            # Date selection for the reporting period.
            with ui.row().classes("items-end gap-4"):
                self.from_picker = ui.date(value=self.start_date.isoformat())
                self.to_picker = ui.date(value=self.end_date.isoformat())

                ui.button("Today", on_click=self._set_today)
                ui.button("Apply", on_click=self._apply_dates)

            # Summary figures populated by refresh().
            with ui.row().classes("w-full gap-4 wrap mt-4"):
                with (
                    ui.card()
                    .classes("flex-1")
                    .tooltip(
                        "Total electricity imported from the grid during the selected period, "
                        "including household consumption and EV charging."
                    )
                ):
                    ui.label("Imported").classes("text-caption")
                    self.imported_label = ui.label("—").classes("text-h6")

                with (
                    ui.card()
                    .classes("flex-1")
                    .tooltip(
                        "Actual Octopus electricity cost for the selected period, "
                        "excluding VAT and using the applicable tariff rates."
                    )
                ):
                    ui.label("Actual cost").classes("text-caption")
                    self.actual_cost_label = ui.label("—").classes("text-h6")

                with (
                    ui.card()
                    .classes("flex-1")
                    .tooltip(
                        "Estimated cost if all imported electricity had been charged "
                        "at the current standard DAY rate."
                    )
                ):
                    ui.label("Normal tariff").classes("text-caption")
                    self.normal_cost_label = ui.label("—").classes("text-h6")

                with (
                    ui.card()
                    .classes("flex-1")
                    .tooltip(
                        "Difference between the normal DAY-rate estimate and actual cost. "
                        "A positive figure means a saving."
                    )
                ):
                    ui.label("Compared with day rate").classes("text-caption")
                    self.saving_label = ui.label("—").classes("text-h6")

                with (
                    ui.card()
                    .classes("flex-1")
                    .tooltip(
                        "The difference expressed as a percentage of the normal DAY-rate cost."
                    )
                ):
                    ui.label("Saving").classes("text-caption")
                    self.saving_percentage_label = ui.label("—").classes("text-h6")

            # ECharts line chart compares actual cost with the normal tariff.
            ui.label("Daily cost").classes("text-subtitle1 mt-4")
            self.cost_chart = ui.echart(
                {
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Actual cost", "Normal tariff"]},
                    "xAxis": {"type": "category", "data": []},
                    "yAxis": {"type": "value", "name": "Cost (£)"},
                    "series": [
                        {
                            "name": "Actual cost",
                            "type": "line",
                            "data": [],
                            "smooth": True,
                        },
                        {
                            "name": "Normal tariff",
                            "type": "line",
                            "data": [],
                            "smooth": True,
                        },
                    ],
                }
            ).classes("w-full h-80")

    def _set_today(self) -> None:
        """Set both date controls to today and refresh the summary."""
        today = date.today()
        self.from_picker.value = today.isoformat()
        self.to_picker.value = today.isoformat()
        self.refresh()

    def _apply_dates(self) -> None:
        """Apply the dates currently selected in the date controls."""
        self.refresh()

    def refresh_live_energy(self) -> None:
        """Refresh the live telemetry cards and current energy-cost estimate.

        Reads the latest stored telemetry snapshot. If no snapshot is available,
        the power labels are reset to placeholders. Otherwise, values and status
        colours are updated according to the existing power-sign conventions.
        """
        snapshot = self.telemetry_repo.get_latest_snapshot()

        # Get and display both current tariff rates independently of telemetry.
        import_rate, export_rate = self.energy_cost_service.get_current_rates()

        import_text = (
            f"Import: {import_rate:.2f}p/kWh"
            if import_rate is not None
            else "Import: unavailable"
        )

        export_text = (
            f"Export: {export_rate:.2f}p/kWh"
            if export_rate is not None
            else "Export: unavailable"
        )

        self.energy_cost_rate_label.set_text(f"{import_text}\n{export_text}")

        if snapshot is None:
            self.pv_label.set_text("—")
            self.battery_label.set_text("—")
            self.soc_label.set_text("—")
            self.grid_label.set_text("—")
            self.house_label.set_text("—")

            self.energy_cost_value_label.set_text("—")
            self.energy_cost_value_label.classes(
                "text-blue",
                remove="text-red text-green text-blue",
            )

            if self.telemetry_source_label:
                self.telemetry_source_label.set_text("Source: no telemetry available")

            return

        # Source and timestamp indicate whether the reading is local Modbus
        # or cloud fallback, and whether a cloud reading is stale.
        source = (
            snapshot["telemetry_source"]
            if "telemetry_source" in snapshot.keys()
            else "Modbus"
        )

        timestamp_text = snapshot["timestamp"]

        try:
            from datetime import datetime

            london_tz = ZoneInfo("Europe/London")
            measured_at = datetime.fromisoformat(timestamp_text)

            if measured_at.tzinfo is None:
                measured_at = measured_at.replace(tzinfo=london_tz)
            else:
                measured_at = measured_at.astimezone(london_tz)

            reading_time = (
                f"{measured_at:%A} {measured_at.day} {measured_at:%B %Y at %H:%M:%S}"
            )

            age_seconds = (datetime.now(london_tz) - measured_at).total_seconds()

        except (TypeError, ValueError):
            reading_time = str(timestamp_text)
            age_seconds = 0

        if source.lower() == "cloud":
            freshness = " • STALE" if age_seconds > 360 else ""
            self.telemetry_source_label.set_text(
                f"Source: Cloud{freshness} • Reading time: {reading_time}"
            )
            self.telemetry_source_label.classes(
                "text-orange",
                remove="text-grey text-green",
            )
        else:
            self.telemetry_source_label.set_text(
                f"Source: Modbus • Reading time: {reading_time}"
            )
            self.telemetry_source_label.classes(
                "text-green",
                remove="text-grey text-orange",
            )

        # Display power magnitudes without signs; status text communicates direction.
        def display_power(value):
            return "—" if value is None else f"{abs(value):.0f} W"

        # PV generation.
        self.pv_label.set_text(display_power(snapshot["solar_w"]))

        # Battery state of charge and its colour thresholds.
        battery_soc = snapshot["battery_soc_pct"]

        self.soc_label.set_text(
            "—" if battery_soc is None else f"{abs(battery_soc):.0f} %"
        )

        if battery_soc is None:
            colour = "text-blue"
        elif battery_soc <= 40:
            colour = "text-red"
        elif battery_soc >= 80:
            colour = "text-green"
        else:
            colour = "text-blue"

        self.soc_label.classes(
            colour,
            remove="text-red text-green text-blue",
        )

        # Battery: positive power = charging; negative power = discharging.
        battery_w = snapshot["battery_w"]
        self.battery_label.set_text(display_power(battery_w))

        if battery_w is None:
            colour, status = "text-blue", "Unavailable"
        elif battery_w == 0:
            colour, status = "text-blue", "Idle"
        elif battery_w < 0:
            colour, status = "text-red", "Discharging"
        else:
            colour, status = "text-green", "Charging"

        self.battery_label.classes(
            colour,
            remove="text-red text-green text-blue",
        )
        self.battery_status_label.set_text(status)
        self.battery_status_label.classes(
            colour,
            remove="text-red text-green text-blue",
        )

        # Grid: positive power = export; negative power = import.
        grid_w = snapshot["grid_w"]
        self.grid_label.set_text(display_power(grid_w))

        if grid_w is None:
            colour, status = "text-blue", "Unavailable"
        elif grid_w == 0:
            colour, status = "text-blue", "Neutral"
        elif grid_w > 0:
            colour, status = "text-green", "Exporting"
        else:
            colour, status = "text-red", "Importing"

        self.grid_label.classes(
            colour,
            remove="text-red text-green text-blue",
        )
        self.grid_status_label.set_text(status)
        self.grid_status_label.classes(
            colour,
            remove="text-red text-green text-blue",
        )

        # House consumption as supplied by the telemetry repository.
        self.house_label.set_text(display_power(snapshot["consumption_w"]))

        # Calculate the current estimated cost or export earnings.
        if grid_w is None:
            current_value = None
            colour = "text-blue"

        elif grid_w < 0:
            # Importing electricity.
            colour = "text-green"

            if import_rate is not None:
                current_value = abs(grid_w) * import_rate / 100_000
            else:
                current_value = None

        elif grid_w > 0:
            # Exporting electricity.
            colour = "text-red"

            if export_rate is not None:
                current_value = grid_w * export_rate / 100_000
            else:
                current_value = None

        else:
            # No grid import or export.
            current_value = 0.0
            colour = "text-blue"

        self.energy_cost_value_label.set_text(
            "—" if current_value is None else f"£{current_value:.2f}/hour"
        )

        # Apply direction colour to Current only.
        self.energy_cost_value_label.classes(
            colour,
            remove="text-red text-green text-blue",
        )

    def refresh(self) -> None:
        """Refresh the selected-period Smart Flex summary and daily chart.

        The date controls define the period for the summary. An inverted date
        range is ignored. The existing implementation also fetches a separate
        daily summary for the Today card.
        """

        # Read the selected date range from the UI controls.
        start_date = date.fromisoformat(self.from_picker.value)
        end_date = date.fromisoformat(self.to_picker.value)
        if start_date > end_date:
            return

        # Retrieve actual Octopus consumption and costs for the selected period.
        tz = ZoneInfo(TIMEZONE)

        period_start = datetime.combine(
            start_date,
            datetime.min.time(),
            tzinfo=tz,
        )

        period_end = datetime.combine(
            end_date + timedelta(days=1),
            datetime.min.time(),
            tzinfo=tz,
        )

        all_costs = self.octopus_repo.get_octopus_consumption_costs()

        print(f"Total stored Octopus records: {len(all_costs)}")

        if not all_costs.empty:
            print("First record:", all_costs["interval_start"].min())
            print("Last record:", all_costs["interval_start"].max())

        costs = self.octopus_repo.get_octopus_consumption_costs(
            period_from=period_start.replace(tzinfo=None).isoformat(),
            period_to=period_end.replace(tzinfo=None).isoformat(),
        )

        print(f"Octopus records returned: {len(costs)}")
        print(costs.head())

        actual_costs = calculate_octopus_actual_costs(costs)
        total = summarise_octopus_actual_costs(actual_costs)

        # Calculate the hypothetical flat DAY-rate comparison.
        day_rate = self.octopus_repo.get_current_import_day_rate()

        if day_rate is not None:
            normal_cost = total["consumption_kwh"] * day_rate / 100
            actual_cost = total["cost_excl_vat_gbp"]

            saving = normal_cost - actual_cost

            saving_percentage = saving / normal_cost * 100 if normal_cost > 0 else 0

            print(f"Current DAY rate: {day_rate:.4f} p/kWh")
            print(f"Normal tariff cost: £{normal_cost:.2f}")
            print(f"Actual cost: £{actual_cost:.2f}")
            print(f"Difference: £{saving:.2f} ({saving_percentage:.1f}%)")
        else:
            normal_cost = None
            saving = None
            saving_percentage = None
            print("No current DAY tariff rate found.")

        # Calculate today's energy and costs using the 30-minute aggregates.
        energy_summary = self.energy_cost_service.get_daily_summary()

        # Energy breakdown.
        self.energy_cost_energy_import_label.set_text(
            f"Import: {energy_summary.energy_import_kwh:.2f} kWh"
        )
        self.energy_cost_energy_export_label.set_text(
            f"Export: {energy_summary.energy_export_kwh:.2f} kWh"
        )
        self.energy_cost_energy_net_label.set_text(
            f"Net: {energy_summary.energy_net_kwh:.2f} kWh"
        )

        # Financial breakdown.
        self.energy_cost_import_cost_label.set_text(
            f"Import: £{energy_summary.import_cost_gbp:.2f}"
        )
        self.energy_cost_export_earnings_label.set_text(
            f"Export: £{energy_summary.export_earnings_gbp:.2f}"
        )
        self.energy_cost_net_cost_label.set_text(
            f"Net: £{energy_summary.net_cost_gbp:.2f}"
        )

        # Colour only the net energy figure.
        if energy_summary.energy_net_kwh > 0.001:
            energy_colour = "text-red"
        elif energy_summary.energy_net_kwh < -0.001:
            energy_colour = "text-green"
        else:
            energy_colour = "text-blue"

        self.energy_cost_energy_net_label.classes(
            energy_colour,
            remove="text-red text-green text-blue",
        )

        # Colour only the net financial figure.
        if energy_summary.net_cost_gbp > 0.001:
            cost_colour = "text-red"
        elif energy_summary.net_cost_gbp < -0.001:
            cost_colour = "text-green"
        else:
            cost_colour = "text-blue"

        self.energy_cost_net_cost_label.classes(
            cost_colour,
            remove="text-red text-green text-blue",
        )

        # Update the summary cards.
        self.imported_label.set_text(f"{total['consumption_kwh']:.1f} kWh")
        self.actual_cost_label.set_text(f"£{total['cost_excl_vat_gbp']:.2f}")

        if normal_cost is not None:
            self.normal_cost_label.set_text(f"£{normal_cost:.2f}")
            self.saving_label.set_text(f"£{saving:.2f}")
            self.saving_percentage_label.set_text(f"{saving_percentage:.1f}%")
        else:
            self.normal_cost_label.set_text("Unavailable")
            self.saving_label.set_text("—")
            self.saving_percentage_label.set_text("—")

        # Update the daily cost comparison chart.
        if not actual_costs.empty and day_rate is not None:
            daily = actual_costs.copy()

            daily["date"] = pd.to_datetime(daily["interval_start"]).dt.date

            daily_summary = (
                daily.groupby("date")
                .agg(
                    actual_cost=("cost_excl_vat_gbp", "sum"),
                    consumption=("consumption_kwh", "sum"),
                )
                .reset_index()
            )

            dates = [d.strftime("%d %b") for d in daily_summary["date"]]
            actual_daily = daily_summary["actual_cost"].round(2).tolist()
            normal_daily = (
                (daily_summary["consumption"] * day_rate / 100).round(2).tolist()
            )

            self.cost_chart.options["xAxis"]["data"] = dates
            self.cost_chart.options["series"][0]["data"] = actual_daily
            self.cost_chart.options["series"][1]["data"] = normal_daily
            self.cost_chart.update()
        else:
            self.cost_chart.options["xAxis"]["data"] = []
            self.cost_chart.options["series"][0]["data"] = []
            self.cost_chart.options["series"][1]["data"] = []
            self.cost_chart.update()
