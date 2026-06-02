# =========================================================
# FILE
# =========================================================
#
# poller/charts/analytics/calculations.py
#
# =========================================================

"""
Telemetry Calculations
======================

Purpose
-------
Reusable derived telemetry calculations.

This module centralizes calculation logic so it
does not become duplicated across:

- loggers
- dashboards
- analytics scripts
- SQL exports
- APIs

Telemetry Semantics
-------------------

Battery Power
    positive = charging
    negative = discharging

Grid Power
    positive = export
    negative = import
"""

# =========================================================
# HOUSE LOAD
# =========================================================


def calculate_house_load_w(
    pv_power_w: float,
    grid_power_w: float,
    battery_power_w: float,
) -> float:
    """
    Calculate estimated house load.

    Formula
    -------
    house_load_w =
        pv_power_w
        - grid_power_w
        - battery_power_w

    Parameters
    ----------
    pv_power_w:
        Solar generation power

    grid_power_w:
        positive = export
        negative = import

    battery_power_w:
        positive = charging
        negative = discharging

    Returns
    -------
    float
        Estimated house consumption load.
    """

    return (
        pv_power_w
        - grid_power_w
        - battery_power_w
    )