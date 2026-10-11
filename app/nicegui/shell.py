from nicegui import ui

from app.nicegui.components.navigation_panel import NavigationPanel
from app.nicegui.navigation import PAGE_REGISTRY
from app.nicegui.components.header import Header
from app.nicegui.components.status_bar import StatusBar


class DashboardShell:
    def __init__(self):

        self.page_container = None
        self.navigation_panel = None
        self.navigation_expanded = True
        self.navigation_title = None
        self.navigation_footer = None
        self.navigation_labels = []
        self.navigation_items = {}
        self.current_page = None
        self.icon_color = "blue"
        self.build()

    def build(self):
        with ui.column().classes("w-screen h-screen gap-0"):
            Header(self.toggle_navigation)
            with ui.row().classes("w-full flex-grow no-wrap items-stretch gap-0"):
                self.navigation = NavigationPanel(
                    PAGE_REGISTRY,
                    self.show_page,
                )
                with ui.column().classes("flex-grow p-6"):
                    self.page_container = ui.column().classes("w-full")
            self.status_bar = StatusBar()
        self.show_page("Overview")


    def toggle_navigation(self):
        self.navigation.toggle()


    def show_page(self, page_name):
        self.navigation.select_page(page_name)
        self.page_container.clear()
        page = PAGE_REGISTRY[page_name]["class"]()
        with self.page_container:
            page.render(self)
