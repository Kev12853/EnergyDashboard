from datetime import date, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from app.octopus.costs.octopus_tariff_matching import (
    get_tariffs_for_period,
    match_tariff_from_periods,
)

from nicegui import ui

from app.connections.connection import get_connection
from app.octopus.costs.octopus_cost_analysis import (
    get_smart_flex_summary,
    get_daily_smart_flex_summary,
)
from app.octopus.storage.repository import OctopusRepository
from app.solax.storage.solax_repository import TelemetryRepository


class OverviewPage:
    def __init__(self) -> None:
        self.octopus_repo = OctopusRepository()

        today = date.today()

        self.start_date = today - timedelta(days=6)
        self.end_date = today

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

        self.energy_cost_status_label = None
        self.energy_cost_value_label = None
        self.energy_cost_rate_label = None
        self.energy_cost_today_label = None

        self.cost_chart = None

        self.connection = get_connection()
        self.telemetry_repo = TelemetryRepository(self.connection)

    def render(self, shell) -> None:
        self.shell = shell
        ui.label("Overview").classes("text-h5")
        self._create_octopus_section()
        self.refresh_live_energy()
        self.refresh()
        ui.timer(
            30,
            self.refresh_live_energy,
        )
        ui.timer(
            300,
            self.refresh,
        )

    def _create_octopus_section(self) -> None:

        with ui.card().classes("w-full"):
            ui.label("Current Energy Status").classes("text-h6")
            self.telemetry_source_label = ui.label("Source: —").classes("text-caption text-grey")

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

        with ui.card().classes("w-full"):
            ui.label("Energy Cost").classes("text-h6")

            with ui.row().classes("w-full gap-4 wrap"):
                with ui.card().classes("flex-1"):
                    ui.label("Current").classes("text-caption")
                    self.energy_cost_value_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("Rate").classes("text-caption")
                    self.energy_cost_rate_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("Status").classes("text-caption")
                    self.energy_cost_status_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("Today").classes("text-caption")
                    self.energy_cost_today_label = ui.label("—").classes("text-h6")

        with ui.card().classes("w-full"):
            ui.label("Octopus Energy").classes("text-h6")

            # -----------------------------------------
            # Date selection
            # -----------------------------------------

            with ui.row().classes("items-end gap-4"):
                self.from_picker = ui.date(
                    value=self.start_date.isoformat(),
                )

                self.to_picker = ui.date(
                    value=self.end_date.isoformat(),
                )

                ui.button(
                    "Today",
                    on_click=self._set_today,
                )

                ui.button(
                    "Apply",
                    on_click=self._apply_dates,
                )

            # -----------------------------------------
            # Summary figures
            # -----------------------------------------

            with ui.row().classes("w-full gap-4 wrap mt-4"):
                with ui.card().classes("flex-1"):
                    ui.label("Imported").classes("text-caption")
                    self.imported_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("Actual cost").classes("text-caption")
                    self.actual_cost_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("Normal tariff").classes("text-caption")
                    self.normal_cost_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("Smart Flex saving").classes("text-caption")
                    self.saving_label = ui.label("—").classes("text-h6")

                with ui.card().classes("flex-1"):
                    ui.label("Saving").classes("text-caption")
                    self.saving_percentage_label = ui.label("—").classes("text-h6")

            # -----------------------------------------
            # Daily cost chart
            # -----------------------------------------

            ui.label("Daily cost").classes("text-subtitle1 mt-4")

            self.cost_chart = ui.echart(
                {
                    "tooltip": {
                        "trigger": "axis",
                    },
                    "legend": {
                        "data": [
                            "Actual cost",
                            "Normal tariff",
                        ],
                    },
                    "xAxis": {
                        "type": "category",
                        "data": [],
                    },
                    "yAxis": {
                        "type": "value",
                        "name": "Cost (£)",
                    },
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
        today = date.today()

        self.from_picker.value = today.isoformat()
        self.to_picker.value = today.isoformat()

        self.refresh()

    def _apply_dates(self) -> None:
        self.refresh()

    def calculate_today_energy_cost(self) -> float:
        """
        Calculate today's live energy cost/earning from SolaX telemetry.

        Negative grid power = import.
        Positive grid power = export.

        Returns:
            Net value in GBP.
            Import is negative.
            Export is positive.
        """

        now = pd.Timestamp.now(
            tz="Europe/London"
        )

        start = now.normalize()

        history = self.telemetry_repo.get_1m_history(
            start=start.tz_localize(None),
            end=now.tz_localize(None),
        )

        if not history:
            return 0.0

        print(
            "GRID TELEMETRY:",
            [
                (
                    row["bucket_start"],
                    row["avg_grid_w"],
                )
                for row in history[:10]
            ],
        )

        print(
            "GRID RANGE:",
            min(row["avg_grid_w"] for row in history),
            max(row["avg_grid_w"] for row in history),
        )

        import_tariff_code = (
            self.octopus_repo.get_current_import_tariff()
        )

        export_tariff_code = (
            self.octopus_repo.get_current_export_tariff()
        )

        import_tariffs = get_tariffs_for_period(
            tariff_code=import_tariff_code,
            period_start=start.to_pydatetime(),
            period_end=now.to_pydatetime(),
            include_vat=True,
        )

        export_tariffs = get_tariffs_for_period(
            tariff_code=export_tariff_code,
            period_start=start.to_pydatetime(),
            period_end=now.to_pydatetime(),
            include_vat=True,
        )

        print(
            "IMPORT TARIFFS:",
            len(import_tariffs),
            import_tariffs[:3],
        )

        print(
            "EXPORT TARIFFS:",
            len(export_tariffs),
            export_tariffs[:3],
        )

        total_gbp = 0.0

        interval_count = 0
        import_kwh = 0.0
        export_kwh = 0.0
        import_cost_gbp = 0.0
        export_earnings_gbp = 0.0
        unmatched_import = 0
        unmatched_export = 0

        for row in history:

            grid_w = row["avg_grid_w"]

            if grid_w == 0:
                continue

            period_start = pd.Timestamp(
                row["bucket_start"],
                tz="Europe/London",
            ).to_pydatetime()

            energy_kwh = (
                abs(grid_w) / 1000 / 60
            )
            
            interval_count += 1

            if grid_w < 0:
                tariff = match_tariff_from_periods(
                    import_tariffs,
                    period_start,
                )

                if tariff is not None:
                    cost = energy_kwh * tariff["rate_p_per_kwh"] / 100

                    import_kwh += energy_kwh
                    import_cost_gbp += cost
                    total_gbp -= cost
                else:
                    unmatched_import += 1

            else:
                tariff = match_tariff_from_periods(
                    export_tariffs,
                    period_start,
                )

                if tariff is not None:
                    earnings = energy_kwh * tariff["rate_p_per_kwh"] / 100

                    export_kwh += energy_kwh
                    export_earnings_gbp += earnings
                    total_gbp += earnings
                else:
                    unmatched_export += 1

        print(
            "TODAY ENERGY DIAGNOSTICS:",
            f"intervals={interval_count}",
            f"import_kwh={import_kwh:.3f}",
            f"import_cost=£{import_cost_gbp:.4f}",
            f"unmatched_import={unmatched_import}",
            f"export_kwh={export_kwh:.3f}",
            f"export_earnings=£{export_earnings_gbp:.4f}",
            f"unmatched_export={unmatched_export}",
            f"net=£{total_gbp:.4f}",
        )

        return total_gbp

    def refresh_live_energy(self) -> None:
        snapshot = self.telemetry_repo.get_latest_snapshot()
        if snapshot is None:
            self.pv_label.set_text("—")
            self.battery_label.set_text("—")
            self.soc_label.set_text("—")
            self.grid_label.set_text("—")
            self.house_label.set_text("—")
            if self.telemetry_source_label:
                self.telemetry_source_label.set_text("Source: no telemetry available")
            return

        source = snapshot["telemetry_source"] if "telemetry_source" in snapshot.keys() else "Modbus"
        timestamp_text = snapshot["timestamp"]
        try:
            from datetime import datetime
            measured_at = datetime.fromisoformat(timestamp_text)
            reading_time = measured_at.strftime("%H:%M:%S")
            age_seconds = (datetime.now() - measured_at).total_seconds()
        except (TypeError, ValueError):
            reading_time = str(timestamp_text)
            age_seconds = 0

        if source.lower() == "cloud":
            freshness = " • STALE" if age_seconds > 360 else ""
            self.telemetry_source_label.set_text(
                f"Source: Cloud{freshness} • Reading time: {reading_time}"
            )
            self.telemetry_source_label.classes("text-orange", remove="text-grey text-green")
        else:
            self.telemetry_source_label.set_text(
                f"Source: Modbus • Reading time: {reading_time}"
            )
            self.telemetry_source_label.classes("text-green", remove="text-grey text-orange")

        def display_power(value):
            return "—" if value is None else f"{abs(value):.0f} W"

        # PV
        self.pv_label.set_text(display_power(snapshot["solar_w"]))

        # State of charge
        battery_soc = snapshot["battery_soc_pct"]
        self.soc_label.set_text("—" if battery_soc is None else f"{abs(battery_soc):.0f} %")
        if battery_soc is None:
            colour = "text-blue"
        elif battery_soc <= 40:
            colour = "text-red"
        elif battery_soc >= 80:
            colour = "text-green"
        else:
            colour = "text-blue"
        self.soc_label.classes(colour, remove="text-red text-green text-blue")

        # Battery: positive = charging; negative = discharging
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
        self.battery_label.classes(colour, remove="text-red text-green text-blue")
        self.battery_status_label.set_text(status)
        self.battery_status_label.classes(colour, remove="text-red text-green text-blue")

        # Grid: positive = export; negative = import
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
        self.grid_label.classes(colour, remove="text-red text-green text-blue")
        self.grid_status_label.set_text(status)
        self.grid_status_label.classes(colour, remove="text-red text-green text-blue")

        # House consumption
        self.house_label.set_text(display_power(snapshot["consumption_w"]))

        # Energy cost based on grid exchange
        import_rate = self.octopus_repo.get_current_import_rate()
        export_rate = self.octopus_repo.get_current_export_rate()

        if grid_w is None:
            status = "Unavailable"
            self.energy_cost_value_label.set_text("—")
            self.energy_cost_rate_label.set_text("—")
            colour = "text-blue"
        elif grid_w < 0:
            rate = import_rate
            status = "Importing"
            colour = "text-red"
            if rate is not None:
                cost_per_hour = (abs(grid_w) / 1000) * (rate / 100)
                self.energy_cost_value_label.set_text(f"£{cost_per_hour:.2f}/hour")
                self.energy_cost_rate_label.set_text(f"{rate:.2f}p/kWh")
            else:
                self.energy_cost_value_label.set_text("—")
                self.energy_cost_rate_label.set_text("—")
        elif grid_w > 0:
            rate = export_rate
            status = "Exporting"
            colour = "text-green"
            if rate is not None:
                value_per_hour = (grid_w / 1000) * (rate / 100)
                self.energy_cost_value_label.set_text(f"£{value_per_hour:.2f}/hour")
                self.energy_cost_rate_label.set_text(f"{rate:.2f}p/kWh")
            else:
                self.energy_cost_value_label.set_text("—")
                self.energy_cost_rate_label.set_text("—")
        else:
            status = "Neutral"
            colour = "text-blue"
            self.energy_cost_value_label.set_text("£0.00/hour")
            self.energy_cost_rate_label.set_text("—")

        self.energy_cost_status_label.set_text(status)
        for label in (
            self.energy_cost_value_label,
            self.energy_cost_rate_label,
            self.energy_cost_status_label,
            self.energy_cost_today_label,
        ):
            label.classes(colour, remove="text-red text-green text-blue")

    def refresh(self) -> None:

##
        # today_cost = self.calculate_today_energy_cost()
        # print(
        #     "TODAY LIVE ENERGY COST:",
        #     f"£{today_cost:.4f}",
        # )
##

        start_date = date.fromisoformat(
            self.from_picker.value,
        )
        end_date = date.fromisoformat(
            self.to_picker.value,
        )
        if start_date > end_date:
            return

        tariff_code = self.octopus_repo.get_comparison_import_tariff()
        # print("OVERVIEW TARIFF CODE:", tariff_code)
        summary = get_smart_flex_summary(
            self.octopus_repo,
            tariff_code,
            start_date=start_date,
            end_date=end_date,
        )
        today_summary = get_daily_smart_flex_summary(
            self.octopus_repo,
            tariff_code,
        )

        total = summary["total"]
        daily = summary["daily"]
        self.energy_cost_today_label.set_text(
            f"£{today_summary['actual_cost_gbp']:.2f}"
        )

        # -----------------------------------------
        # Summary figures
        # -----------------------------------------

        self.imported_label.set_text(f"{total['consumption_kwh']:.1f} kWh")
        self.actual_cost_label.set_text(f"£{total['actual_cost_gbp']:.2f}")
        self.normal_cost_label.set_text(f"£{total['normal_cost_gbp']:.2f}")
        self.saving_label.set_text(f"£{total['smart_flex_saving_gbp']:.2f}")
        self.saving_percentage_label.set_text(f"{total['saving_percentage']:.1f}%")

        # -----------------------------------------
        # Chart
        # -----------------------------------------

        dates = [row.strftime("%d %b") for row in daily["date"]]

        actual_costs = [float(value) for value in daily["actual_cost_gbp"]]

        normal_costs = [float(value) for value in daily["normal_cost_gbp"]]

        self.cost_chart.options["xAxis"]["data"] = dates

        self.cost_chart.options["series"][0]["data"] = actual_costs

        self.cost_chart.options["series"][1]["data"] = normal_costs

        self.cost_chart.update()
