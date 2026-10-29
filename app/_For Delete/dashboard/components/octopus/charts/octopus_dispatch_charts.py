import altair as alt
import pandas as pd
import streamlit as st


def render_dispatch_timeline(
    dispatch_df: pd.DataFrame,
):

    if dispatch_df.empty:
        st.info("No dispatch data available.")

        return

    with st.expander(
        "🔌 Intelligent Charging Schedule",
        expanded=True,
    ):
        timeline = (
            alt.Chart(dispatch_df)
            .mark_bar(cornerRadius=5)
            .encode(
                x=alt.X(
                    "dispatch_start:T",
                    title="Time (London)",
                ),
                x2="dispatch_end:T",
                y=alt.Y(
                    "status:N",
                    title=None,
                ),
                color=alt.Color(
                    "status:N",
                    scale=alt.Scale(
                        domain=[
                            "Completed",
                            "Planned",
                        ],
                        range=[
                            "#2ecc71",
                            "#3498db",
                        ],
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "dispatch_start:T",
                        format="%H:%M",
                        title="Start",
                    ),
                    alt.Tooltip(
                        "dispatch_end:T",
                        format="%H:%M",
                        title="End",
                    ),
                    alt.Tooltip(
                        "scheduled_energy_kwh:Q",
                        title="Est. kWh",
                    ),
                ],
            )
            .properties(height=120)
        )

        now_line = (
            alt.Chart(pd.DataFrame({"now": [pd.Timestamp.now()]}))
            .mark_rule(
                color="red",
                strokeDash=[4, 4],
            )
            .encode(x="now:T")
        )

        st.altair_chart(
            timeline + now_line,
            width="stretch",
        )
