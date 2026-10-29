"""Build and manage the shared shell of the NiceGUI Energy Dashboard.

The shell provides the common structure around every dashboard page:
    - Header
    - Navigation panel
    - Main page container
    - Status bar

Available pages are supplied by ``PAGE_REGISTRY`` from
``app.nicegui.navigation``. Selecting a page clears the current page container,
constructs the selected page class and renders it into that container.

This module coordinates UI components; it does not implement individual page
contents or the underlying telemetry and automation services.
"""

from nicegui import ui

# Shared UI components used to build the application frame.
from app.nicegui.components.navigation_panel import NavigationPanel
from app.nicegui.navigation import PAGE_REGISTRY
from app.nicegui.components.header import Header
from app.nicegui.components.status_bar import StatusBar


class DashboardShell:
    """Construct and coordinate the common dashboard layout.

    The shell holds references to the main UI containers and navigation state.
    It delegates page selection to the navigation panel and page construction
    to the classes registered in ``PAGE_REGISTRY``.
    """

    def __init__(self):
        """Initialise shell state and build the initial dashboard layout.

        Attributes are initialised before ``build()`` creates the UI. Some are
        retained as shell state for navigation or layout behaviour; this class
        does not itself define the contents of individual pages.
        """
        self.page_container = None
        self.navigation_panel = None
        self.navigation_expanded = True
        self.navigation_title = None
        self.navigation_footer = None
        self.navigation_labels = []
        self.navigation_items = {}
        self.current_page = None
        self.icon_color = "blue"

        # Create the shared layout and display the initial page.
        self.build()

    def build(self):
        """Create the header, navigation area, page container and status bar.

        The navigation panel receives the page registry and the callback used
        when a user chooses a page. The page container is cleared and reused
        when navigating, rather than creating a separate permanent container
        for each page.
        """
        # The outer column fills the available browser viewport.
        with ui.column().classes("w-screen h-screen gap-0"):
            # The header receives a callback so it can toggle navigation.
            Header(self.toggle_navigation)

            # The main row places navigation beside the content area.
            with ui.row().classes("w-full flex-grow no-wrap items-stretch gap-0"):
                self.navigation = NavigationPanel(
                    PAGE_REGISTRY,
                    self.show_page,
                )

                # Pages render into this reusable column.
                with ui.column().classes("flex-grow p-6"):
                    self.page_container = ui.column().classes("w-full")

            # The shared status bar appears beneath the main content.
            self.status_bar = StatusBar()

        # Display the default page once the shell has been constructed.
        self.show_page("Overview")

    def toggle_navigation(self):
        """Toggle the navigation panel's expanded/collapsed state.

        The actual presentation and state change are handled by
        ``NavigationPanel``.
        """
        self.navigation.toggle()

    def show_page(self, page_name):
        """Display the page registered under ``page_name``.

        Args:
            page_name: Key identifying a page in ``PAGE_REGISTRY``.

        The navigation panel is updated, the previous page's UI elements are
        removed, and a fresh instance of the registered page class is rendered
        into the shared page container.

        The method expects ``page_name`` to exist in ``PAGE_REGISTRY``; an
        unknown name raises ``KeyError``. Page-specific rendering errors are
        allowed to propagate rather than being silently hidden.
        """
        # Keep the navigation selection in sync with the displayed page.
        self.navigation.select_page(page_name)

        # Remove the old page's UI before rendering the new one.
        self.page_container.clear()

        # Registry entries store the page class under the "class" key.
        page = PAGE_REGISTRY[page_name]["class"]()

        # Bind rendering to the shared content container.
        with self.page_container:
            page.render(self)
