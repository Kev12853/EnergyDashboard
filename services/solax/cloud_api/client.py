"""
SolaX Cloud API Client
======================

Purpose
-------
Provides a lightweight client wrapper around the SolaX Cloud
realtime telemetry endpoint.

This module is responsible for:

1. Calling the SolaX cloud API
2. Validating API responses
3. Mapping raw SolaX payloads into the project's
   normalized PowerFlowSnapshot model

Design Notes
------------
The rest of the application should NOT depend directly on
raw SolaX JSON field names.

This module acts as a translation layer between:

    SolaX Cloud API
        ->
    PowerFlowSnapshot

This allows future transport mechanisms (Modbus, MQTT, etc.)
to reuse the same canonical telemetry model.

Telemetry Semantics
-------------------

Battery Power
    positive = charging
    negative = discharging

Grid Power
    positive = export to grid
    negative = import from grid

PV Power
    positive = generation

Notes
-----
Cloud telemetry appears to update approximately every
5 minutes even when polled more frequently.

Polling faster is still useful because it allows near-immediate
capture when a new cloud update arrives.
"""

from datetime import datetime

import requests

from services.solax.models import (
    PowerFlowSnapshot,
)


class SolaxCloudClient:
    """
    Client for SolaX Cloud realtime telemetry.
    """

    def __init__(
        self,
        token_id: str,
        serial_number: str,
    ):
        """
        Parameters
        ----------
        token_id:
            SolaX Cloud API token

        serial_number:
            Inverter serial number
        """

        self.token_id = token_id

        self.serial_number = serial_number

        self.base_url = (
            "https://www.solaxcloud.com:9443"
        )

    # =====================================================
    # REALTIME INFO
    # =====================================================

    def get_realtime_info(self):
        """
        Retrieve raw realtime telemetry payload from SolaX Cloud.

        Returns
        -------
        dict
            Raw JSON result payload from SolaX API.

        Raises
        ------
        requests.HTTPError
            If HTTP request fails.

        Exception
            If SolaX API reports an application-level failure.
        """

        url = (
            f"{self.base_url}"
            "/proxy/api/getRealtimeInfo.do"
        )

        params = {
            "tokenId": self.token_id,
            "sn": self.serial_number,
        }

        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):

            raise Exception(
                f"SolaX API Error: "
                f"{data.get('exception')}"
            )

        return data["result"]

    # =====================================================
    # NORMALIZED SNAPSHOT
    # =====================================================

    def get_snapshot(self) -> PowerFlowSnapshot:
        """
        Retrieve normalized telemetry snapshot.

        Returns
        -------
        PowerFlowSnapshot

        Notes
        -----
        The PowerFlowSnapshot model is the canonical
        telemetry representation used throughout the project.

        This prevents the rest of the codebase from becoming
        tightly coupled to raw SolaX field names.
        """

        data = self.get_realtime_info()

        # =================================================
        # PV TOTAL
        # =================================================
        #
        # SolaX exposes PV strings separately.
        # Combine into total PV generation.
        #

        pv1 = data.get("powerdc1") or 0

        pv2 = data.get("powerdc2") or 0

        pv_total = pv1 + pv2

        # =================================================
        # NORMALIZED SNAPSHOT
        # =================================================

        snapshot = PowerFlowSnapshot(

            # =============================================
            # LOCAL POLL TIMESTAMP
            # =============================================

            timestamp=datetime.now(),

            # =============================================
            # INVERTER CLOUD UPDATE TIME
            # =============================================

            upload_time=data.get("uploadTime"),

            # =============================================
            # SOLAR
            # =============================================

            pv_power_w=pv_total,

            pv1_power_w=pv1,

            pv2_power_w=pv2,

            # =============================================
            # BATTERY
            # =============================================

            battery_soc_pct=data.get("soc"),

            battery_power_w=data.get("batPower"),

            battery_status=data.get("batStatus"),

            # =============================================
            # GRID
            # =============================================
            #
            # Convention:
            #
            # positive = export
            # negative = import
            #

            grid_power_w=data.get("feedinpower"),

            # =============================================
            # INVERTER AC OUTPUT
            # =============================================

            ac_power_w=data.get("acpower"),

            # =============================================
            # INVERTER METADATA
            # =============================================

            inverter_status=data.get(
                "inverterStatus"
            ),

            inverter_serial=data.get(
                "inverterSN"
            ),
        )

        return snapshot