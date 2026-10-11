from nicegui import ui


class Header:

    def __init__(self, menu_callback) -> None:

        with ui.row().classes(
            "w-full h-16 bg-blue-700 items-center justify-between px-4 text-white"
        ):

            with ui.row().classes("items-center"):

                ui.button(
                    icon="menu",
                    on_click=menu_callback,
                ).props("flat color=white")

                ui.label("Energy Dashboard").classes("text-h5")