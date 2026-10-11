from datetime import datetime

from nicegui import ui

from app.connections.connection import get_connection
from app.enums.service_enums import ServiceName
from app.nicegui.components.service_status_card import ServiceStatusCard
from app.nicegui.components.status_banner import StatusBanner
from app.nicegui.data.telemetry_repository import TelemetryRepository


class OperationsPage:
    def __init__(self) -> None:

        self.connection = get_connection()
        self.telemetry_repo = TelemetryRepository(self.connection)
        self.poller_status_card = None
        self.aggregator_status_card = None
        self.octopus_status_card = None
        self.shell = None

    def render(self, shell) -> None:

        self.status_banner = StatusBanner()
        self.shell = shell

        # Create the Status Cards
        with ui.row().classes("w-full gap-4 wrap"):
            self.poller_status_card = ServiceStatusCard(
                "Poller",
                ServiceName.POLLER,)
            self.aggregator_status_card = ServiceStatusCard(
                "Aggregator",
                ServiceName.AGGREGATOR,
            )
            self.octopus_status_card = ServiceStatusCard(
                "Octopus",
                ServiceName.OCTOPUS,
            )

        # Populate immediately
        self.refresh()

        # Refresh every 30 seconds
        ui.timer(
            30,
            self.refresh,
        )

    def _get_heartbeats(
        self,
    ) -> dict[ServiceName, datetime | None]:

        return {
            service: self.telemetry_repo.get_heartbeat(service)
            for service in (
                ServiceName.POLLER,
                ServiceName.AGGREGATOR,
                ServiceName.OCTOPUS,
            )
        }

    def refresh(self) -> None:

        # Get the heartbeats of all the services
        heartbeats = self._get_heartbeats()
        # Update the Banner
        self.status_banner.set_status(heartbeats)
        # Update the Service Cards
        self.poller_status_card.set_status(heartbeats[ServiceName.POLLER])
        self.aggregator_status_card.set_status(heartbeats[ServiceName.AGGREGATOR])
        self.octopus_status_card.set_status(heartbeats[ServiceName.OCTOPUS])
        # Update the Status Bar
        self.shell.status_bar.set_status(heartbeats)