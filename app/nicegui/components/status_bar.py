from datetime import datetime

from nicegui import ui

from app.enums.service_enums import ServiceName, HeartbeatAge, ServiceState



class StatusBar:

    def __init__(self) -> None:

        self.icons: dict[ServiceName, ui.icon] = {}
        with ui.row().classes(
            "w-full h-9 bg-blue-700 text-white "
            "items-center justify-around px-3"
        ):
            self._add_status_item(
                ServiceName.POLLER,
                "Poller",
            )
            self._add_status_item(
                ServiceName.AGGREGATOR,
                "Aggregator",
            )
            self._add_status_item(
                ServiceName.OCTOPUS,
                "Octopus",
            )

    # ------------------------------------------------------------------

    def _add_status_item(
        self,
        service_name: ServiceName,
        label: str,
    ) -> None:

        with ui.row().classes("items-center gap-1"):
            icon = (
                ui.icon("check_circle")
                .classes("text-green-400 text-sm")
            )
            ui.label(label).classes("text-sm")
            self.icons[service_name] = icon

    # ------------------------------------------------------------------

    def set_status(
        self,
        heartbeats: dict[ServiceName, datetime | None],
    ) -> None:

        for service_name, last_seen in heartbeats.items():
            status = self._get_status(
                service_name,
                last_seen,
            )
            icon = self.icons[service_name]
            icon.classes(
                remove=(
                    "text-green-400 "
                    "text-yellow-400 "
                    "text-red-400"
                )
            )
            if status == ServiceState.RUNNING:
                icon.props("name=check_circle")
                icon.classes(add="text-green-400")
            elif status == ServiceState.WARNING:
                icon.props("name=warning")
                icon.classes(add="text-yellow-400")
            else:
                icon.props("name=error")
                icon.classes(add="text-red-400")

    # ------------------------------------------------------------------

    def _get_status(
        self,
        service_name: ServiceName,
        last_seen: datetime | None,
    ) -> ServiceState:

        if last_seen is None:
            return ServiceState.STOPPED
        running_timeout = HeartbeatAge[
            service_name.name
        ].value
        warning_timeout = running_timeout * 2
        age = (
            datetime.now() - last_seen
        ).total_seconds()
        if age < running_timeout:
            return ServiceState.RUNNING
        if age < warning_timeout:
            return ServiceState.WARNING
        return ServiceState.STOPPED