"""Registry of pages available in the NiceGUI Energy Dashboard.

Each entry in ``PAGE_REGISTRY`` maps a user-visible page name to:
    - ``title``: the label shown in the navigation UI.
    - ``class``: the page class instantiated when the page is selected.
    - ``icon``: the icon identifier used by the navigation component.

The dashboard shell imports this registry and passes it to ``NavigationPanel``.
When a page is selected, ``DashboardShell.show_page`` retrieves the class from
the matching entry and calls its ``render()`` method.

Adding a page normally requires importing its page class and adding an entry
here. The page class itself is responsible for rendering its own content.

This module defines which pages are registered; it does not implement the
navigation UI or the page contents.
"""

# Import the page classes that are available to the application navigation.
# These imports also mean that their modules are loaded when this registry is
# imported, so each page module must be importable at application startup.
from app.nicegui.pages.health import HealthPage
from app.nicegui.pages.octopus import OctopusPage
from app.nicegui.pages.operations import OperationsPage
from app.nicegui.pages.overview import OverviewPage


class Menu:
    """Placeholder class retained from the existing implementation.

    There are no attributes or methods defined here, and ``PAGE_REGISTRY``
    does not currently use this class. Before removing it, check the project
    for references elsewhere.
    """
    pass


# Central registry used by DashboardShell and NavigationPanel.
# The keys are the page names passed to DashboardShell.show_page().
PAGE_REGISTRY = {
    "Overview": {
        "title": "Overview",       # Display label for the page.
        "class": OverviewPage,     # Class instantiated to render the page.
        "icon": "home",            # Navigation icon identifier.
    },
    "Operations": {
        "title": "Operations",
        "class": OperationsPage,
        "icon": "settings",
    },
    "Health": {
        "title": "Health",
        "class": HealthPage,
        "icon": "monitor_heart",
    },
    "Octopus": {
        "title": "Octopus",
        "class": OctopusPage,
        "icon": "bolt",
    },
}
