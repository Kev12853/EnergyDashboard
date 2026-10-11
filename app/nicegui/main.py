from nicegui import ui

from app.nicegui.shell import DashboardShell

ui.add_head_html("""
<style>

.nicegui-content {
    padding: 0 !important;
}

</style>
""")

DashboardShell()

ui.run()