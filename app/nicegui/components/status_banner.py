from datetime import datetime

from nicegui import ui

from app.enums.service_enums import ServiceName, HeartbeatAge, ServiceState


class StatusBanner:

    def __init__(self) -> None:
        self._icon_class = ""
        self._banner_class = ""

        with ui.card().classes("w-full rounded-xl shadow-sm q-pa-lg") as self.banner:
            with ui.row().classes("items-center no-wrap"):
                self.icon = ui.icon("circle").classes("text-4xl")
                self.text = (
                    ui.label("Unknown")
                    .classes("text-h4 font-bold q-ml-md")
                )

    # ------------------------------------------------------------------

    def set_status(
        self,
        heartbeats: dict[ServiceName, datetime | None],
    ) -> None:

        overall_status = ServiceState.RUNNING
        for service_name, last_seen in heartbeats.items():
            if last_seen is None:
                status = ServiceState.STOPPED
            else:
                running_timeout = HeartbeatAge[
                    service_name.name
                ].value

                warning_timeout = running_timeout * 2

                age = (
                    datetime.now() - last_seen
                ).total_seconds()
                if age < running_timeout:
                    status = ServiceState.RUNNING
                elif age < warning_timeout:
                    status = ServiceState.WARNING
                else:
                    status = ServiceState.STOPPED

            overall_status = max(
                overall_status,
                status,
            )

        if overall_status == ServiceState.RUNNING:
            text = "Operating Normally"
            icon = "check_circle"
            icon_classes = "text-green-600"
            banner_classes = (
                "bg-green-50 border border-green-500"
            )
        elif overall_status == ServiceState.WARNING:
            text = "Operating with Warnings"
            icon = "warning"
            icon_classes = "text-yellow-600"
            banner_classes = (
                "bg-yellow-50 border border-yellow-500"
            )
        else:
            text = "Service Failure"
            icon = "error"
            icon_classes = "text-red-600"
            banner_classes = (
                "bg-red-50 border border-red-500"
            )
        self._update_display(
            text,
            icon,
            icon_classes,
            banner_classes,
        )

    # ------------------------------------------------------------------

    def _update_display(
        self,
        text: str,
        icon: str,
        icon_classes: str,
        banner_classes: str,
    ) -> None:

        if self._icon_class:
            self.icon.classes(remove=self._icon_class)
        if self._banner_class:
            self.banner.classes(remove=self._banner_class)
        self.icon.props(f"name={icon}")
        self.text.set_text(text)
        self.icon.classes(add=icon_classes)
        self.banner.classes(add=banner_classes)
        self._icon_class = icon_classes
        self._banner_class = banner_classes