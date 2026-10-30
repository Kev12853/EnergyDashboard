"""Evaluate dispatch, vehicle and battery conditions for Smart Flex charging. This controller makes a decision from supplied inputs; the control service and orchestrator persist requests, and the reconciler handles inverter writes."""

from datetime import datetime, timedelta, timezone

import pandas as pd

from app.config.solax_config import SMART_FLEX_SOC_TARGET
from app.enums.solax_enums import WorkMode, ManualMode
from app.logging.logger import setup_logger


logger = setup_logger("Smart Flex Controller")


class SmartFlexController:

    """Evaluate active dispatch, connected/charging vehicle status and battery SOC to decide whether Force Charge should start for a half-hour slot."""
    def __init__(self):
        self.current_slot_start = None
        self.force_charge_active = False

    def get_active_dispatch(self, dispatches, timestamp):
        """Select the dispatch whose UTC start/end interval contains timestamp; return None for missing, empty or non-matching rows."""
        if dispatches is None or dispatches.empty:
            return None

        # Compare absolute instants. Stripping an offset can select the wrong
        # half-hour slot around daylight-saving transitions.
        timestamp = timestamp.replace(tzinfo=timestamp.tzinfo or timezone.utc)
        timestamp = timestamp.astimezone(timezone.utc)
        starts = pd.to_datetime(dispatches["dispatch_start"], utc=True)
        ends = pd.to_datetime(dispatches["dispatch_end"], utc=True)

        active = dispatches[(starts <= timestamp) & (ends > timestamp)]

        if active.empty:
            return None

        return active.iloc[0]

    def evaluate(
        self,
        snapshot,
        dispatch,
        vehicle_status,
    ):
        """
        Evaluate Smart Flex conditions.

        A new 30-minute cost slot causes a fresh decision.

        If Force Charge starts during a slot, it remains active for
        the remainder of that slot. BMW status is therefore only used
        to START Force Charge, not to stop it during the slot.

        Returns:

            "FORCE_CHARGE"
            "NORMAL"
        """

        now = snapshot.timestamp

        # ------------------------------------------------------------
        # Determine the current 30-minute cost slot
        # ------------------------------------------------------------

        slot_minute = 0 if now.minute < 30 else 30

        slot_start = now.replace(
            minute=slot_minute,
            second=0,
            microsecond=0,
        )

        new_slot = self.current_slot_start != slot_start

        if new_slot:
            logger.info(f"Smart Flex new cost slot: {slot_start.strftime('%H:%M')}")

            self.current_slot_start = slot_start
            self.force_charge_active = False

        # ------------------------------------------------------------
        # If Force Charge has already been selected for this slot,
        # leave it running until the slot ends.
        # ------------------------------------------------------------

        if self.force_charge_active:
            logger.info("Smart Flex: Force Charge already active for current cost slot")
            return "FORCE_CHARGE"

        # ------------------------------------------------------------
        # We have not started Force Charge for this slot.
        #
        # Check the conditions. These checks are therefore performed
        # on every poll until Force Charge starts or the slot ends.
        # ------------------------------------------------------------

        if dispatch is None:
            logger.info("Smart Flex: no active dispatch")
            return "NORMAL"

        if not vehicle_status.get("connected", False):
            logger.info("Smart Flex: BMW not connected")
            return "NORMAL"

        if not vehicle_status.get("charging", False):
            logger.info("Smart Flex: BMW not charging")
            return "NORMAL"

        # ------------------------------------------------------------
        # Check SolaX battery SOC
        # ------------------------------------------------------------

        soc = snapshot.battery_soc_pct

        if soc is None:
            logger.info("Smart Flex: battery SOC unavailable")
            return "NORMAL"

        logger.info(f"Smart Flex: BMW charging, SolaX SOC={soc:.1f}%")

        if soc >= SMART_FLEX_SOC_TARGET:
            logger.info(
                f"Smart Flex: SOC target reached "
                f"({soc:.1f}% >= {SMART_FLEX_SOC_TARGET}%)"
            )
            return "NORMAL"

        # ------------------------------------------------------------
        # All conditions satisfied.
        #
        # Latch Force Charge for the remainder of this cost slot.
        # ------------------------------------------------------------

        slot_end = slot_start + timedelta(minutes=30)

        logger.info(
            f"Smart Flex: starting Force Charge for "
            f"{slot_start.strftime('%H:%M')}-"
            f"{slot_end.strftime('%H:%M')}"
        )

        self.force_charge_active = True

        return "FORCE_CHARGE"

    def reset(self):
        """Clear the in-memory slot latch; durable ownership and inverter state remain managed by the orchestrator/repository."""
        self.current_slot_start = None
        self.force_charge_active = False
