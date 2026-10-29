"""Render Octopus completed and planned dispatches as a NiceGUI timeline chart.

The chart uses ECharts custom rectangles to show dispatch intervals and exposes
scheduled energy and interval times in each block's tooltip.
"""

import pandas as pd
from nicegui import ui


class DispatchTimeline:
    """Build a timeline chart from completed and planned dispatch data.

    DataFrames are retained at construction and copied during rendering so
    date conversion does not mutate the repository-provided DataFrames.
    """

    def __init__(
        self,
        completed_df: pd.DataFrame,
        planned_df: pd.DataFrame,
        completed_hours: int = 24,
    ) -> None:
        """Store dispatch data and the number of completed-history hours.

        Args:
            completed_df: Completed dispatches to display.
            planned_df: Planned dispatches to display.
            completed_hours: Width of the chart's historical time window.
        """
        self.completed_df = completed_df
        self.planned_df = planned_df
        self.completed_hours = completed_hours

    def render(self) -> None:
        """Prepare dispatch intervals and render the ECharts timeline.

        Completed and planned intervals occupy separate horizontal rows.
        Dispatch times are converted to milliseconds for the browser chart.
        """
        # -------------------------------------------------
        # Prepare data
        # -------------------------------------------------

        completed = self.completed_df.copy()
        planned = self.planned_df.copy()

        # Normalize timestamp columns on the local copies only.
        for df in (completed, planned):

            if not df.empty:

                df["dispatch_start"] = pd.to_datetime(
                    df["dispatch_start"]
                )

                df["dispatch_end"] = pd.to_datetime(
                    df["dispatch_end"]
                )

        # -------------------------------------------------
        # Chart range
        #
        # Start = selected completed history
        # End   = latest planned dispatch
        # -------------------------------------------------

        now = pd.Timestamp.now()

        chart_start = (
            now
            - pd.Timedelta(
                hours=self.completed_hours
            )
        )

        if not planned.empty:

            chart_end = planned[
                "dispatch_end"
            ].max()

        elif not completed.empty:

            chart_end = completed[
                "dispatch_end"
            ].max()

        else:

            chart_end = now

        # Make sure the chart has a useful future extent

        if chart_end <= now:

            chart_end = (
                now
                + pd.Timedelta(hours=1)
            )

        # -------------------------------------------------
        # Build chart data
        #
        # Row 0 = Completed
        # Row 1 = Planned
        #
        # [start, end, row, status, energy]
        # -------------------------------------------------

        # ECharts receives [start_ms, end_ms, row_index, status, energy_kwh].
        # Row 0 is completed history; row 1 is planned dispatches.
        series_data = []

        for _, row in completed.iterrows():

            start_ms = int(
                row["dispatch_start"].timestamp()
                * 1000
            )

            end_ms = int(
                row["dispatch_end"].timestamp()
                * 1000
            )

            energy = row[
                "scheduled_energy_kwh"
            ]

            if pd.isna(energy):

                energy = None

            else:

                energy = float(energy)

            series_data.append(
                [
                    start_ms,
                    end_ms,
                    0,
                    "Completed",
                    energy,
                ]
            )

        for _, row in planned.iterrows():

            start_ms = int(
                row["dispatch_start"].timestamp()
                * 1000
            )

            end_ms = int(
                row["dispatch_end"].timestamp()
                * 1000
            )

            energy = row[
                "scheduled_energy_kwh"
            ]

            if pd.isna(energy):

                energy = None

            else:

                energy = float(energy)

            series_data.append(
                [
                    start_ms,
                    end_ms,
                    1,
                    "Planned",
                    energy,
                ]
            )

        # -------------------------------------------------
        # Empty / partial state
        # -------------------------------------------------

        if not series_data:
            ui.label("No dispatches scheduled for this period.").classes(
                "text-gray-500 text-center w-full py-8"
            )

            return

        if completed.empty:
            ui.label("No completed dispatches in the selected period.").classes(
                "text-gray-500 text-sm mb-2"
            )

        # -------------------------------------------------
        # ECharts
        # -------------------------------------------------

        # ECharts custom-series configuration draws each dispatch as a
        # rectangle spanning its start and end timestamps.
        options = {

            "animation": False,

            "grid": {
                "left": 90,
                "right": 30,
                "top": 25,
                "bottom": 45,
            },

            # ---------------------------------------------
            # Tooltip
            # ---------------------------------------------

            "tooltip": {
                "trigger": "item",

                ":formatter": (
                    "function(params) {"

                    "const v = params.value;"

                    "const start = "
                    "new Date(v[0]);"

                    "const end = "
                    "new Date(v[1]);"

                    "const fmt = d => "
                    "d.toLocaleString([], {"
                    "day: '2-digit',"
                    "month: 'short',"
                    "hour: '2-digit',"
                    "minute: '2-digit'"
                    "});"

                    "return '<b>' + v[3] + "
                    "'</b><br>'"
                    "+ fmt(start)"
                    "+ ' – '"
                    "+ fmt(end)"
                    "+ '<br>Scheduled energy: '"
                    "+ (v[4] == null"
                    "+ ? '—'"
                    "+ : v[4].toFixed(3)"
                    "+ ' kWh');"

                    "}"
                ),
            },

            # ---------------------------------------------
            # X axis
            # ---------------------------------------------

            "xAxis": {

                "type": "time",

                "min": int(
                    chart_start.timestamp()
                    * 1000
                ),

                "max": int(
                    chart_end.timestamp()
                    * 1000
                ),

                "axisLabel": {

                    "hideOverlap": True,

                    ":formatter": (
                        "function(value) {"

                        "return new Date(value)"
                        ".toLocaleString([], {"
                        "day: '2-digit',"
                        "month: 'short',"
                        "hour: '2-digit',"
                        "minute: '2-digit'"
                        "});"

                        "}"
                    ),
                },

                "splitLine": {
                    "show": True,
                },
            },

            # ---------------------------------------------
            # Y axis
            # ---------------------------------------------

            "yAxis": {

                "type": "category",

                "data": [
                    "Completed",
                    "Planned",
                ],

                "inverse": True,
            },

            # ---------------------------------------------
            # Dispatch blocks
            # ---------------------------------------------

            "series": [
                {

                    "type": "custom",

                    ":renderItem": (
                        "function(params, api) {"

                        "const start = api.coord(["
                        "api.value(0),"
                        "api.value(2)"
                        "]);"

                        "const end = api.coord(["
                        "api.value(1),"
                        "api.value(2)"
                        "]);"

                        "const rowHeight = "
                        "api.size([0, 1])[1];"

                        "const height = "
                        "rowHeight * 0.55;"

                        "return {"

                        "type: 'rect',"

                        "shape: {"

                        "x: start[0],"

                        "y: start[1]"
                        " - height / 2,"

                        "width: Math.max("
                        "end[0] - start[0],"
                        "4"
                        "),"

                        "height: height"

                        "},"

                        "style: {"

                        "fill: "
                        "api.value(3)"
                        " === 'Completed'"
                        " ? '#4caf50'"
                        " : '#2196f3'",

                        "stroke: '#333'",

                        "lineWidth: 1"

                        "}"

                        "};"

                        "}"
                    ),

                    "encode": {
                        "x": [0, 1],
                        "y": 2,
                    },

                    "data": series_data,
                }
            ],
        }

        # -------------------------------------------------
        # Render chart only
        # -------------------------------------------------

        ui.echart(
            options
        ).classes(
            "w-full"
        ).style(
            "height: 220px;"
        )