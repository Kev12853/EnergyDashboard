"""NiceGUI health page for telemetry, automation, inverter, and database status.

The page reads the latest local telemetry snapshot and automation periods, then
presents a high-level status summary. Status thresholds are based on the age of
the latest telemetry record; this page is diagnostic and does not control the
inverter.
"""

from datetime import datetime, timezone

from nicegui import ui

from app.connections.connection import get_connection
from app.enums.automation_enums import InverterWorkMode
from app.nicegui.data.automation_repository import AutomationRepository
from app.nicegui.data.telemetry_repository import TelemetryRepository
from app.nicegui.helpers import decode_work_mode


class HealthPage:
    """Render and refresh the system health view."""

    def __init__(self) -> None:
        """Create repository instances and initialise UI element references."""
        # These repositories use the application's configured database connection.
        self.telemetry_repo = TelemetryRepository(get_connection())
        self.automation_repo = AutomationRepository(get_connection())

        # References are populated by render() before refresh() is called.
        self.shell = None
        self.banner = None
        self.card_automation = None

    # ------------------------------------------------------------------

    def render(self, shell) -> None:
        """Build the health banner and the four diagnostic cards."""
        self.shell = shell
        # Retained commented heading from the original implementation:
        # ui.label("System Health").classes("text-h4 font-bold")

        # The banner summarises the age of the latest telemetry snapshot.
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

        # Cards report telemetry age, automation configuration, inverter mode,
        # and a basic database connectivity check.
        with ui.grid(columns=2).classes("w-full gap-4"):
            # Poller / telemetry card
            with ui.card().classes("w-full rounded-xl shadow-sm"):
                ui.label("⚡ Poller").classes("text-h6 font-bold")
                ui.separator()
                with ui.row().classes("w-full justify-between"):
                    ui.label("Telemetry Age")
                    self.label_telemetry_age = ui.label("--")
                with ui.row().classes("w-full justify-between"):
                    ui.label("Status")
                    self.label_poller_status = ui.label("--")

            # Automation configuration counts
            with ui.card().classes("w-full rounded-xl shadow-sm"):
                ui.label("⚙ Automation").classes("text-h6 font-bold")
                ui.separator()
                with ui.row().classes("w-full justify-between"):
                    ui.label("Configured Periods")
                    self.label_configured_periods = ui.label("--")
                with ui.row().classes("w-full justify-between"):
                    ui.label("Enabled Periods")
                    self.label_enabled_periods = ui.label("--")

            # Inverter mode is read from the latest telemetry snapshot.
            with ui.card().classes("w-full rounded-xl shadow-sm"):
                ui.label("🔌 Inverter").classes("text-h6 font-bold")
                ui.separator()
                with ui.row().classes("w-full justify-between"):
                    ui.label("Work Mode")
                    self.label_work_mode_card = ui.label("--")
                with ui.row().classes("w-full justify-between"):
                    ui.label("Connection")
                    self.label_inverter_connection = ui.label("--")

            # The database check below tests whether a simple query succeeds.
            with ui.card().classes("w-full rounded-xl shadow-sm"):
                ui.label("💾 Database").classes("text-h6 font-bold")
                ui.separator()
                with ui.row().classes("w-full justify-between"):
                    ui.label("Connection")
                    self.label_database_connection = ui.label("--")
                with ui.row().classes("w-full justify-between"):
                    ui.label("Telemetry")
                    self.label_database_telemetry = ui.label("--")

        # Populate the newly created UI immediately.
        self.refresh()

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Read current database values and update the health indicators.

        Telemetry younger than 5 minutes is Healthy; 5–30 minutes is Delayed;
        30 minutes or older is Offline. The same 5-minute threshold is used
        for the inverter connection and telemetry freshness labels.
        """
        # The current page depends on a local telemetry snapshot being available.
        latest_snapshot = self.telemetry_repo.get_latest_snapshot()

        if latest_snapshot is None:
            self.icon.props("name=error")
            self.label_banner_status.set_text("No live telemetry available")
            return

        # Parse the stored timestamp and calculate its age against UTC now.
        latest_timestamp = datetime.fromisoformat(latest_snapshot["timestamp"])
        last_update = latest_timestamp.strftime("%d %b %H:%M")

        data_age_minutes = (
            datetime.now(timezone.utc) - latest_timestamp
        ).total_seconds() / 60

        # Choose banner wording, icon, and styling based on telemetry age.
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

        # Remove previous status colours before applying the current ones.
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

        # Poller card: reports the age and derived status of the latest snapshot.
        self.label_telemetry_age.set_text(f"{data_age_minutes:.1f} minutes")
        self.label_poller_status.set_text(status)

        # Automation card: count all configured periods and those enabled.
        periods = self.automation_repo.get_periods()
        enabled = sum(1 for period in periods if period.enabled)
        self.label_configured_periods.set_text(str(len(periods)))
        self.label_enabled_periods.set_text(str(enabled))

        # Inverter card: translate the stored work-mode code into readable text.
        work_mode = decode_work_mode(latest_snapshot["work_mode"])
        work_mode_text = work_mode.name.replace("_", " ").title()
        self.label_work_mode_card.set_text(work_mode_text)
        self.label_work_mode.set_text(f"⚡ {work_mode_text}")

        # Retained commented-out alternative from the original implementation:
        # self.label_work_mode.set_text(f"⚡ {work_mode}")
        if data_age_minutes < 5:
            connection_status = "Online"
        else:
            connection_status = "Offline"
        self.label_inverter_connection.set_text(connection_status)

        # A minimal query verifies that the database connection is responsive.
        try:
            self.telemetry_repo.connection.execute("SELECT 1").fetchone()
            database_status = "Operational"
        except Exception:
            database_status = "Unavailable"

        # This is based on telemetry age, not a separate database-table check.
        if data_age_minutes < 5:
            telemetry_status = "Current"
        else:
            telemetry_status = "Stale"

        self.label_database_connection.set_text(database_status)
        self.label_database_telemetry.set_text(telemetry_status)
