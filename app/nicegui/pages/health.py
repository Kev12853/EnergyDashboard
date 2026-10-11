from datetime import datetime, timezone

from nicegui import ui

from app.connections.connection import get_connection
from app.enums.automation_enums import InverterWorkMode
from app.nicegui.data.automation_repository import AutomationRepository
from app.nicegui.data.telemetry_repository import TelemetryRepository
from app.nicegui.helpers import decode_work_mode


class HealthPage:
    def __init__(self) -> None:

        self.telemetry_repo = TelemetryRepository(get_connection())
        self.automation_repo = AutomationRepository(get_connection())
        self.shell = None
        self.banner = None
        self.card_automation = None

    # ------------------------------------------------------------------

    def render(self, shell) -> None:

        self.shell = shell
        # ui.label("System Health").classes("text-h4 font-bold")

        # Create Default Banner
        with ui.card().classes("w-full rounded-xl shadow-sm") as self.banner:
            with ui.row().classes("items-center no-wrap"):
                self.icon = ui.icon("check_circle").classes("text-3xl")
                self.label_banner = ui.label("System").classes("text-h5 font-bold")
                self.label_banner_status = ui.label("Initialising").classes(
                    "text-h6 font-bold"
                )
                self.label_work_mode = ui.label("").classes("text-subtitle1")
                self.label_last_update = ui.label("Last Update").classes(
                    "text-subtitle1"
                )
                self.label_last_update_time = ui.label("").classes("text-subtitle1")

        # Setup Grid for Cards
        with ui.grid(columns=2).classes("w-full gap-4"):
            # Create Default Poller Card
            with ui.card().classes("w-full rounded-xl shadow-sm"):
                ui.label("⚡ Poller").classes("text-h6 font-bold")
                ui.separator()
                with ui.row().classes("w-full justify-between"):
                    ui.label("Telemetry Age")
                    self.label_telemetry_age = ui.label("--")
                with ui.row().classes("w-full justify-between"):
                    ui.label("Status")
                    self.label_poller_status = ui.label("--")

            # Create Default Automation Card
            with ui.card().classes("w-full rounded-xl shadow-sm"):
                ui.label("⚙ Automation").classes("text-h6 font-bold")
                ui.separator()
                with ui.row().classes("w-full justify-between"):
                    ui.label("Configured Periods")
                    self.label_configured_periods = ui.label("--")
                with ui.row().classes("w-full justify-between"):
                    ui.label("Enabled Periods")
                    self.label_enabled_periods = ui.label("--")

            # Create Default Inverter Card
            with ui.card().classes("w-full rounded-xl shadow-sm"):
                ui.label("🔌 Inverter").classes("text-h6 font-bold")
                ui.separator()
                with ui.row().classes("w-full justify-between"):
                    ui.label("Work Mode")
                    self.label_work_mode_card = ui.label("--")
                with ui.row().classes("w-full justify-between"):
                    ui.label("Connection")
                    self.label_inverter_connection = ui.label("--")

            # Create Default Database Card
            with ui.card().classes("w-full rounded-xl shadow-sm"):
                ui.label("💾 Database").classes("text-h6 font-bold")
                ui.separator()
                with ui.row().classes("w-full justify-between"):
                    ui.label("Connection")
                    self.label_database_connection = ui.label("--")
                with ui.row().classes("w-full justify-between"):
                    ui.label("Telemetry")
                    self.label_database_telemetry = ui.label("--")

        self.refresh()

    # ------------------------------------------------------------------

    def refresh(self) -> None:

        # Get latest snapshot
        latest_snapshot = self.telemetry_repo.get_latest_snapshot()

        if latest_snapshot is None:
            self.icon.props("name=error")
            self.label_banner_status.set_text("No live telemetry available")
            return

        # Set variables
        latest_timestamp = datetime.fromisoformat(latest_snapshot["timestamp"])
        last_update = latest_timestamp.strftime("%d %b %H:%M")

        data_age_minutes = (
            datetime.now(timezone.utc) - latest_timestamp
        ).total_seconds() / 60

        if data_age_minutes < 5:
            status = "Healthy"
            icon = "check_circle"
            icon_classes = "text-green-600"
            banner_classes = "bg-green-50 border border-green-500"
        elif data_age_minutes < 30:
            status = "Delayed"
            icon = "warning"
            icon_classes = "text-yellow-600"
            banner_classes = "bg-yellow-50 border border-yellow-500"
        else:
            status = "Offline"
            icon = "error"
            icon_classes = "text-red-600"
            banner_classes = "bg-red-50 border border-red-500"

        # Update Banner
        self.banner.classes(
            remove=(
                "bg-green-50 "
                "bg-yellow-50 "
                "bg-red-50 "
                "border "
                "border-green-500 "
                "border-yellow-500 "
                "border-red-500"
            )
        )
        self.icon.classes(remove=("text-green-600 text-yellow-600 text-red-600"))
        self.banner.classes(add=banner_classes)
        self.icon.classes(add=icon_classes)
        self.icon.props(f"name={icon}")

        self.label_banner_status.set_text(f"{status}")
        self.label_last_update_time.set_text(f"{last_update}")

        # Update Poller Card
        self.label_telemetry_age.set_text(f"{data_age_minutes:.1f} minutes")
        self.label_poller_status.set_text(status)

        # Update Automation Card
        periods = self.automation_repo.get_periods()
        enabled = sum(1 for period in periods if period.enabled)
        self.label_configured_periods.set_text(str(len(periods)))
        self.label_enabled_periods.set_text(str(enabled))

        # Update Inverter Card
        work_mode = decode_work_mode(latest_snapshot["work_mode"])
        work_mode_text = work_mode.name.replace("_", " ").title()
        self.label_work_mode_card.set_text(work_mode_text)
        self.label_work_mode.set_text(f"⚡ {work_mode_text}")

        # self.label_work_mode.set_text(f"⚡ {work_mode}")
        if data_age_minutes < 5:
            connection_status = "Online"
        else:
            connection_status = "Offline"
        self.label_inverter_connection.set_text(connection_status)

        # Update Database Card
        try:
            self.telemetry_repo.connection.execute("SELECT 1").fetchone()
            database_status = "Operational"
        except Exception:
            database_status = "Unavailable"

        if data_age_minutes < 5:
            telemetry_status = "Current"
        else:
            telemetry_status = "Stale"

        self.label_database_connection.set_text(database_status)
        self.label_database_telemetry.set_text(telemetry_status)
