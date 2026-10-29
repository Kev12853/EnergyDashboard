"""Application entry point for the Energy Dashboard's NiceGUI interface.

This module starts the web application and delegates dashboard construction to
:class:`app.nicegui.shell.DashboardShell`.

Responsibilities:
    - Import NiceGUI's UI API.
    - Construct the dashboard shell, which builds the shared layout and pages.
    - Start the NiceGUI server.

The page layout and navigation logic live in ``app.nicegui.shell`` and the
modules it imports. This entry point intentionally contains very little
application logic.

Background services (such as telemetry polling) may be started separately;
this file does not explicitly start them.
"""

from nicegui import ui

# DashboardShell owns the shared application layout, navigation and page area.
from app.nicegui.shell import DashboardShell

# Apply a small global CSS adjustment before constructing the page layout.
# Removing the default content padding allows the shell's own layout classes
# to control spacing.
ui.add_head_html("""
<style>
.nicegui-content {
    padding: 0 !important;
}
</style>
""")

# Build the dashboard header, navigation panel, page container and status bar.
# DashboardShell also selects the initial Overview page.
DashboardShell()

# Start the NiceGUI web server. This call normally keeps the application running.
ui.run()
