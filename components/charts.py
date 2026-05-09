import streamlit as st
import altair as alt

# -----------------------
# ENERGY CHART
# -----------------------
def energy_chart(df, freq):
    if freq is None:
        time_format = "%d %b %Y %H:%M"
    else:
        time_format = "%d %b %Y"

    st.subheader("Energy Flow")

    df = df.copy()

    # X axis
    if freq is None:

        x = alt.X(
            "datetime:T",
            title="Date / Time"
        )

    else:

        df["date_label"] = (
            df["datetime"]
            .dt.strftime("%d %b")
        )

        x = alt.X(
            "date_label:N",
            title="Date"
        )

    # -----------------------
    # SEPARATE DATASETS
    # -----------------------
    df_consumption = df.copy()
    df_consumption["series"] = "Consumption"

    df_export = df.copy()
    df_export["series"] = "Export"

    # -----------------------
    # CONSUMPTION BARS
    # -----------------------
    consumption = (
        alt.Chart(df_consumption)
        .mark_bar(
            color="#3498db",
            opacity=0.7
        )
        .encode(
            x=x,
            xOffset=alt.XOffset(
                "series:N"
            ),
            y=alt.Y(
                "consumption_kwh:Q",
                title="Consumption (kWh)",
                axis=alt.Axis(
                    titleColor="#3498db",
                    orient="left"
                )
            ),
            tooltip=[
                alt.Tooltip(
                    "datetime:T",
                    title="Time"
                ),
                alt.Tooltip(
                    "consumption_kwh:Q",
                    title="Consumption",
                    format=".3f"
                )
            ]
        )
    )

    # -----------------------
    # EXPORT BARS
    # -----------------------
    export = (
        alt.Chart(df_export)
        .mark_bar(
            color="#2ecc71",
            opacity=0.7
        )
        .encode(
            x=x,
            xOffset=alt.XOffset(
                "series:N"
            ),
            y=alt.Y(
                "export_kwh:Q",
                title="Export (kWh)",
                axis=alt.Axis(
                    titleColor="#2ecc71",
                    orient="right"
                )
            ),
            tooltip=[
                alt.Tooltip(
                    "datetime:T",
                    title="Time",
                    format=time_format
                ),
                alt.Tooltip(
                    "export_kwh:Q",
                    title="Export",
                    format=".3f"
                )
            ]
        )
    )

    chart = (
        alt.layer(
            consumption,
            export
        )
        .resolve_scale(
            y="independent"
        )
        .properties(height=400)
    )

    st.altair_chart(
        chart,
        width="stretch"    )


# -----------------------
# FINANCIAL CHART
# -----------------------
def financial_chart(df, freq):

    st.subheader("Financial Impact")

    df = df.copy()

    # -----------------------
    # X AXIS
    # -----------------------
    if freq is None:

        x = alt.X(
            "datetime:T",
            title="Date / Time"
        )

        time_format = "%d %b %Y %H:%M"

    else:

        df["date_label"] = (
            df["datetime"]
            .dt.strftime("%d %b")
        )

        x = alt.X(
            "date_label:N",
            title="Date"
        )

        time_format = "%d %b %Y"

    # -----------------------
    # RESHAPE DATA
    # -----------------------
    chart_df = df.melt(
        id_vars=["datetime"],
        value_vars=[
            "revenue",
            "net"
        ],
        var_name="series",
        value_name="value"
    )

    chart_df["series"] = (
        chart_df["series"]
        .str.capitalize()
    )

    # Add labels for aggregated views
    if freq is not None:

        chart_df["date_label"] = (
            chart_df["datetime"]
            .dt.strftime("%d %b")
        )

    # -----------------------
    # CHART
    # -----------------------
    chart = (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=3,
            point={
                "size": 10,
                "filled": True
            }
        )
        .encode(
            x=x,

            y=alt.Y(
                "value:Q",
                title="Financial (£)"
            ),

            color=alt.Color(
                "series:N",
                title="Series",
                scale=alt.Scale(
                    domain=["Revenue", "Net"],
                    range=["green", "orange"]
                )
            ),

            tooltip=[
                alt.Tooltip(
                    "datetime:T",
                    title="Time",
                    format=time_format
                ),

                alt.Tooltip(
                    "series:N",
                    title="Series"
                ),

                alt.Tooltip(
                    "value:Q",
                    title="Value (£)",
                    format=".2f"
                )
            ]
        )
        .properties(height=400)
    )

    st.altair_chart(
        chart,
        width="stretch"
    )