from datetime import datetime

from nicegui import ui

from app.enums.service_enums import ServiceName, HeartbeatAge, ServiceState



class ServiceStatusCard:

    def __init__(
        self,
        title: str,
        service_name: ServiceName,
    ) -> None:

        self.service_name = service_name
        self._status_class = ""
        with ui.card().classes("flex-1"):
            ui.label(title).classes("text-h6 font-bold")
            ui.separator()
            with ui.row().classes("justify-between w-full"):
                ui.label("Status")
                self.status = ui.label("Unknown")
            with ui.row().classes("justify-between w-full"):
                ui.label("Last Seen")
                self.label_last_seen = ui.label("--")

    # ------------------------------------------------------------------

    def set_status(
        self,
        last_seen: datetime | None,
    ) -> ServiceState:

        # Service has never reported
        if last_seen is None:
            status = ServiceState.STOPPED
            classes = "text-red-600"
        else:
            # Calculate heartbeat age
            running_timeout = HeartbeatAge[
                self.service_name.name
            ].value
            warning_timeout = running_timeout * 2
            age = (
                datetime.now() - last_seen
            ).total_seconds()
            if age < running_timeout:
                status = ServiceState.RUNNING
                classes = "text-green-600"
            elif age < warning_timeout:
                status = ServiceState.WARNING
                classes = "text-yellow-600"
            else:
                status = ServiceState.STOPPED
                classes = "text-red-600"
        # Update status display
        if self._status_class:
            self.status.classes(
                remove=self._status_class
            )
        self.status.set_text(
            status.name.title()
        )
        self.status.classes(add=classes)
        self._status_class = classes
        # Update last seen display
        if last_seen is None:
            self.label_last_seen.set_text("--")
        else:
            self.label_last_seen.set_text(
                last_seen.strftime("%d %b %H:%M")
            )
        return status