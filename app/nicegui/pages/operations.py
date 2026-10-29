"""Operations page showing the health of background application services.

The page displays heartbeat information for three services:
    - Poller
    - Aggregator
    - Octopus

It uses ``TelemetryRepository`` to retrieve each service's most recent heartbeat,
then updates a status banner, individual service cards and the shell's shared
status bar. The page refreshes every 30 seconds.

This module presents service status; it does not start, stop or restart services.
The heartbeat data is produced by the services themselves.
"""

from datetime import datetime

from nicegui import ui

# Shared database connection and service identifiers.
from app.connections.connection import get_connection
from app.enums.service_enums import ServiceName

# UI components used to display overall and per-service status.
from app.nicegui.components.service_status_card import ServiceStatusCard
from app.nicegui.components.status_banner import StatusBanner

# Repository used by this page to read service heartbeat timestamps.
from app.nicegui.data.telemetry_repository import TelemetryRepository


class OperationsPage:
    """Render the Operations screen and refresh service heartbeat indicators."""

    def __init__(self) -> None:
        """Create the database repository and initialise UI references.

        UI components are assigned during ``render()``. The database connection
        is obtained when the page instance is created.
        """
        self.connection = get_connection()
        self.telemetry_repo = TelemetryRepository(self.connection)

        # These references are populated by render() before refresh() is called.
        self.poller_status_card = None
        self.aggregator_status_card = None
        self.octopus_status_card = None
        self.shell = None

    def render(self, shell) -> None:
        """Build the page and schedule periodic status refreshes.

        Args:
            shell: The DashboardShell hosting this page. The page uses its
                shared status bar to display the same heartbeat information.
        """
        # Overall banner summarises the status of the monitored services.
        self.status_banner = StatusBanner()
        self.shell = shell

        # Create one status card for each monitored background service.
        with ui.row().classes("w-full gap-4 wrap"):
            self.poller_status_card = ServiceStatusCard(
                "Poller",
                ServiceName.POLLER,
            )
            self.aggregator_status_card = ServiceStatusCard(
                "Aggregator",
                ServiceName.AGGREGATOR,
            )
            self.octopus_status_card = ServiceStatusCard(
                "Octopus",
                ServiceName.OCTOPUS,
            )

        # Populate the banner, cards and shell status bar immediately.
        self.refresh()

        # Re-read heartbeat data every 30 seconds while this page is active.
        ui.timer(30, self.refresh)

    def _get_heartbeats(self) -> dict[ServiceName, datetime | None]:
        """Return the latest heartbeat timestamp for each monitored service.

        Returns:
            A mapping from service identifier to its latest heartbeat timestamp,
            or ``None`` when the repository has no heartbeat for that service.
        """
        return {
            service: self.telemetry_repo.get_heartbeat(service)
            for service in (
                ServiceName.POLLER,
                ServiceName.AGGREGATOR,
                ServiceName.OCTOPUS,
            )
        }

    def refresh(self) -> None:
        """Refresh all status indicators from the latest heartbeat data."""
        # Fetch each heartbeat once so all indicators use the same data set.
        heartbeats = self._get_heartbeats()

        # Update the page-level summary banner.
        self.status_banner.set_status(heartbeats)

        # Update each service's individual card.
        self.poller_status_card.set_status(heartbeats[ServiceName.POLLER])
        self.aggregator_status_card.set_status(heartbeats[ServiceName.AGGREGATOR])
        self.octopus_status_card.set_status(heartbeats[ServiceName.OCTOPUS])

        # Keep the shell's persistent status bar in sync with this page.
        self.shell.status_bar.set_status(heartbeats)
