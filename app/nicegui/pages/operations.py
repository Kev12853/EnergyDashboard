from datetime import datetime, timedelta

from nicegui import ui

from app.backend.storage.db import get_connection
from app.enums.service_names import ServiceName
from app.solax.storage.solax_repository import TelemetryRepository


class OperationsPage:
    def __init__(self):
        self.label_poller_status = None
        self.label_poller_last_seen = None

        self.label_aggregator_status = None
        self.label_aggregator_last_seen = None

        self.label_octopus_status = None
        self.label_octopus_last_seen = None

        self.telemetry_repo = TelemetryRepository(get_connection())

    def render(self):

        ui.label("Energy Dashboard").classes("text-h5")
        ui.separator()
        ui.label("Operations").classes("text-h6")

        with ui.row().classes("w-full gap-4"):
            # Poller Card
            with ui.card().classes("flex-1"):
                ui.label("Poller").classes("text-h6 font-bold")
                with ui.row().classes("flex-1 items-baseline"):
                    ui.label("Status: ").classes("text-h7")
                    self.label_poller_status = ui.label("Unknown").classes(
                        "text-h8 text-yellow-500"
                    )
                with ui.row().classes("flex-1 items-baseline"):
                    ui.label("Last Update").classes("text-h7")
                    self.label_poller_last_seen = ui.label("Unknown").classes(
                        "text-h8 text-yellow-500"
                    )

            # Aggregator Card
            with ui.card().classes("flex-1"):
                ui.label("Aggregator").classes("text-h6 font-bold")
                with ui.row().classes("flex-1 items-baseline"):
                    ui.label("Status: ").classes("text-h7")
                    self.label_aggregator_status = ui.label("Unknown").classes(
                        "text-h8 text-yellow-500"
                    )
                with ui.row().classes("flex-1 items-baseline"):
                    ui.label("Last Update").classes("text-h7")
                    self.label_aggregator_last_seen = ui.label("Unknown").classes(
                        "text-h8 text-yellow-500"
                    )

            # Solax Card
            with ui.card().classes("flex-1"):
                ui.label("Octopus").classes("text-h6 font-bold")
                with ui.row().classes("flex-1 items-baseline"):
                    ui.label("Status: ").classes("text-h7")
                    self.label_octopus_status = ui.label("Unknown").classes(
                        "text-h8 text-yellow-500"
                    )
                with ui.row().classes("flex-1 items-baseline"):
                    ui.label("Last Update").classes("text-h7")
                    self.label_octopus_last_seen = ui.label("Unknown").classes(
                        "text-h8 text-yellow-500"
                    )

        self.update_status()
        ui.timer(1, self.update_status)

    def update_status(self):
        self.update_solax()
        self.update_aggregator()
        self.update_octopus()

    def update_solax(self):
        last_seen_poller = self.telemetry_repo.get_heartbeat(ServiceName.POLLER)
        last_seen_agregator = self.telemetry_repo.get_heartbeat(ServiceName.AGGREGATOR)
        last_seen_solax = self.telemetry_repo.get_heartbeat(ServiceName.OCTOPUS)

        if last_seen_poller is None:
            # Never seen
            self.label_poller_status.set_text("🟡 No Data Available")
            self.label_poller_status.classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-yellow-500",
            )
        elif datetime.now() - last_seen_poller < timedelta(minutes=2):
            # Running
            self.label_poller_status.set_text("🟢 Running").classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-green-500",
            )
            self.label_poller_last_seen.set_text(
                f"{last_seen_poller:%b} {last_seen_poller.day}, {last_seen_poller:%H:%M}"
            ).classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-green-500",
            )
        else:
            # Stopped
            self.label_poller_status.set_text("🔴 Stopped")
            self.label_poller_status.classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-red-500",
            )
            self.label_poller_last_seen.set_text(
                last_seen_poller.strftime("%Y-%m-%d %H:%M:%S")
            ).classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-red-500",
            )

    def update_aggregator(self):
        last_seen_aggregator = self.telemetry_repo.get_heartbeat(ServiceName.AGGREGATOR)
        last_seen_solax = self.telemetry_repo.get_heartbeat(ServiceName.OCTOPUS)

        if last_seen_aggregator is None:
            # Never seen
            self.label_aggregator_status.set_text("🟡 No Data Available")
            self.label_aggregator_status.classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-yellow-500",
            )
        elif datetime.now() - last_seen_aggregator < timedelta(minutes=6):
            # Running
            self.label_aggregator_status.set_text("🟢 Running").classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-green-500",
            )
            self.label_aggregator_last_seen.set_text(
                f"{last_seen_aggregator:%b} {last_seen_aggregator.day}, {last_seen_aggregator:%H:%M}"
            ).classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-green-500",
            )
        else:
            # Stopped
            self.label_aggregator_status.set_text("🔴 Stopped")
            self.label_aggregator_status.classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-red-500",
            )
            self.label_aggregator_last_seen.set_text(
                last_seen_aggregator.strftime("%Y-%m-%d %H:%M:%S")
            ).classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-red-500",
            )

    def update_octopus(self):

        last_seen_octopus = self.telemetry_repo.get_heartbeat(ServiceName.OCTOPUS)

        if last_seen_octopus is None:
            # Never seen
            self.label_octopus_status.set_text("🟡 No Data Available")
            self.label_octopus_status.classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-yellow-500",
            )
        elif datetime.now() - last_seen_octopus < timedelta(minutes=1):
            # Running
            self.label_octopus_status.set_text("🟢 Running").classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-green-500",
            )
            self.label_octopus_last_seen.set_text(
                f"{last_seen_octopus:%b} {last_seen_octopus.day}, {last_seen_octopus:%H:%M}"
            ).classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-green-500",
            )
        else:
            # Stopped
            self.label_octopus_status.set_text("🔴 Stopped")
            self.label_octopus_status.classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-red-500",
            )
            self.last_seen_octopus.set_text(
                last_seen_octopus.strftime("%Y-%m-%d %H:%M:%S")
            ).classes(
                remove="text-red-500 text-green-500 text-yellow-500",
                add="text-red-500",
            )


@ui.page("/")
def operations():
    page = OperationsPage()
    page.render()
