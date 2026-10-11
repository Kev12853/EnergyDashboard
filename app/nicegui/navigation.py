from app.nicegui.pages.health import HealthPage
from app.nicegui.pages.octopus import OctopusPage
from app.nicegui.pages.operations import OperationsPage
from app.nicegui.pages.overview import OverviewPage

class Menu:
    pass


PAGE_REGISTRY = {
    "Overview": {
        "title": "Overview",
        "class": OverviewPage,
        "icon": "home",
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