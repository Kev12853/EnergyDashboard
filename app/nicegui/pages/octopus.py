from datetime import date, timedelta

import pandas as pd
from nicegui import ui

from app.nicegui.components.octopus.dispatch_timeline import (
    DispatchTimeline,
)
from app.octopus.storage.repository import OctopusRepository


class OctopusPage:

    def __init__(self) -> None:
        pass

    def render(self, shell) -> None:

        repository = OctopusRepository()

        with ui.column().classes("w-full gap-4"):

            ui.label("Octopus Energy").classes(
                "text-2xl font-bold"
            )

            # =================================================
            # CURRENT INTELLIGENT CHARGING SCHEDULE
            # =================================================

            completed_hours = 24

            range_options = {
                24: "24 Hours",
                48: "48 Hours",
                120: "5 Days",
                240: "10 Days",
                720: "30 Days",
            }

            # -------------------------------------------------
            # Completed history selector
            # -------------------------------------------------

            with ui.row().classes("items-center gap-4 w-full"):
                ui.label("Completed history:").classes("font-medium")

                completed_range = ui.toggle(
                    range_options,
                    value=24,
                ).props("no-caps")

            # -------------------------------------------------
            # Intelligent Charging Schedule
            # -------------------------------------------------

            schedule_expansion = ui.expansion(
                "Intelligent Charging Schedule",
                icon="power",
            ).classes("w-full")

            with schedule_expansion:
                timeline_container = ui.column().classes("w-full")

            def load_current_schedule() -> None:

                print(f"Loading current dispatch schedule ({completed_hours} hours)")

                completed_df, planned_df = repository.get_current_dispatch_schedule(
                    completed_hours=completed_hours,
                )

                print(f"Completed: {len(completed_df)} rows")

                print(f"Planned: {len(planned_df)} rows")

                timeline_container.clear()

                with timeline_container:
                    DispatchTimeline(
                        completed_df,
                        planned_df,
                        completed_hours,
                    ).render()

                print("TIMELINE RENDERED")

            # Initial current schedule load
            load_current_schedule()

            # Explicitly open on first page load
            schedule_expansion.open()


            def select_range(event) -> None:

                nonlocal completed_hours

                completed_hours = int(event.value)

                print(
                    f"Completed history changed to "
                    f"{completed_hours} hours"
                )

                load_current_schedule()

            completed_range.on_value_change(
                select_range
            )

            # -------------------------------------------------
            # Initial current schedule load
            # -------------------------------------------------

            load_current_schedule()

            # =================================================
            # DISPATCH HISTORY
            # =================================================

            today = date.today()

            with ui.expansion(
                "Dispatch History",
                icon="history",
            ).classes("w-full"):

                # ---------------------------------------------
                # Date controls
                # ---------------------------------------------

                with ui.row().classes(
                    "items-end gap-4"
                ):

                    with ui.column():

                        ui.label("From")

                        start_date = ui.date(
                            value=today
                            - timedelta(days=7),
                        )

                    with ui.column():

                        ui.label("To")

                        end_date = ui.date(
                            value=today,
                        )

                    apply_history_button = ui.button(
                        "Apply",
                        icon="refresh",
                    )

                # ---------------------------------------------
                # Table container
                # ---------------------------------------------

                history_container = ui.column().classes(
                    "w-full"
                )

                def load_history() -> None:

                    if (
                        not start_date.value
                        or not end_date.value
                    ):
                        return

                    start = (
                        pd.to_datetime(
                            start_date.value
                        ).date()
                    )

                    end = (
                        pd.to_datetime(
                            end_date.value
                        ).date()
                    )

                    if start > end:

                        ui.notify(
                            "From date must be before To date.",
                            type="warning",
                        )

                        return

                    print(
                        "Loading dispatch history "
                        f"{start} to {end}"
                    )

                    dispatch_df = (
                        repository.get_dispatch_history(
                            start_date=start,
                            end_date=end,
                        )
                    )

                    print(
                        "Dispatch history returned "
                        f"{len(dispatch_df)} rows"
                    )

                    history_container.clear()

                    with history_container:

                        if dispatch_df.empty:

                            ui.label(
                                "No dispatch history found "
                                "for this period."
                            ).classes(
                                "text-gray-500"
                            )

                            return

                        # -------------------------------------
                        # Prepare table data
                        # -------------------------------------

                        table_df = dispatch_df.copy()

                        table_df[
                            "dispatch_start"
                        ] = (
                            table_df[
                                "dispatch_start"
                            ].dt.strftime(
                                "%d %b %Y %H:%M"
                            )
                        )

                        table_df[
                            "dispatch_end"
                        ] = (
                            table_df[
                                "dispatch_end"
                            ].dt.strftime(
                                "%d %b %Y %H:%M"
                            )
                        )

                        table_df[
                            "first_seen"
                        ] = (
                            table_df[
                                "first_seen"
                            ].dt.strftime(
                                "%d %b %Y %H:%M:%S"
                            )
                        )

                        table_df[
                            "last_seen"
                        ] = (
                            table_df[
                                "last_seen"
                            ].dt.strftime(
                                "%d %b %Y %H:%M:%S"
                            )
                        )

                        rows = (
                            table_df[
                                [
                                    "id",
                                    "dispatch_start",
                                    "dispatch_end",
                                    "scheduled_energy_kwh",
                                    "status",
                                    "first_seen",
                                    "last_seen",
                                ]
                            ]
                            .to_dict(
                                orient="records"
                            )
                        )

                        columns = [
                            {
                                "name": "id",
                                "label": "ID",
                                "field": "id",
                                "align": "left",
                            },
                            {
                                "name": "dispatch_start",
                                "label": "Start",
                                "field": "dispatch_start",
                                "align": "left",
                                "sortable": True,
                            },
                            {
                                "name": "dispatch_end",
                                "label": "End",
                                "field": "dispatch_end",
                                "align": "left",
                                "sortable": True,
                            },
                            {
                                "name": (
                                    "scheduled_energy_kwh"
                                ),
                                "label": "Scheduled kWh",
                                "field": (
                                    "scheduled_energy_kwh"
                                ),
                                "align": "right",
                                "sortable": True,
                            },
                            {
                                "name": "status",
                                "label": "Status",
                                "field": "status",
                                "align": "left",
                                "sortable": True,
                            },
                            {
                                "name": "first_seen",
                                "label": "First Seen",
                                "field": "first_seen",
                                "align": "left",
                                "sortable": True,
                            },
                            {
                                "name": "last_seen",
                                "label": "Last Seen",
                                "field": "last_seen",
                                "align": "left",
                                "sortable": True,
                            },
                        ]

                        ui.table(
                            columns=columns,
                            rows=rows,
                            row_key="id",
                            pagination={
                                "rowsPerPage": 20,
                            },
                        ).classes(
                            "w-full"
                        )

                # ---------------------------------------------
                # History controls
                # ---------------------------------------------

                apply_history_button.on_click(
                    load_history
                )

                # ---------------------------------------------
                # Initial history load
                # ---------------------------------------------

                load_history()

            # =================================================
            # TARIFFS
            # =================================================

            with ui.expansion(
                "Tariffs",
                icon="payments",
            ).classes("w-full"):

                ui.label(
                    "Tariff information will appear here."
                ).classes("text-gray-500")