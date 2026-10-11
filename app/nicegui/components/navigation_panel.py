from nicegui import ui


class NavigationPanel:

    def __init__(
        self,
        page_registry,
        page_selected_callback,
    ) -> None:
        self.page_registry = page_registry
        self.page_selected_callback = page_selected_callback
        self.navigation_expanded = True
        self.current_page = None
        self.navigation_labels = []
        self.navigation_items = {}
        #self.navigation_title = None
        self.navigation_footer = None
        self.container = ui.column()

        self.build()

    def build(self) -> None:
        self.container.classes("h-full bg-grey-2 border-r").style(
            "width:180px; transition:width .25s ease;"
        )
        with self.container:
                with ui.column().classes("h-full w-full gap-0"):
                    # Branding
                    # with ui.row().classes("w-full h-16 items-center px-5"):
                    #     ui.icon("bolt").classes("text-3xl text-blue-700")
                    #     self.navigation_title = (
                    #         ui.label("Energy")
                    #         .classes("text-subtitle1")
                    #         .style(
                    #             "width:120px;"
                    #             "margin-left:16px;"
                    #             "margin-bottom:16px;"
                    #             "opacity:1;"
                    #             "transition:opacity .15s ease;"
                    #         )
                    #     )
                    # Menu
                    with ui.column().classes("w-full p-2 gap-1"):
                        for page_name, page in self.page_registry.items():
                            with ui.item(
                                on_click=lambda name=page_name: self.page_selected_callback(name)
                            ).classes(
                                "w-full rounded-lg cursor-pointer transition-all duration-200 hover:bg-blue-100"
                            ) as item:
                                with ui.item_section().props("avatar"):
                                    ui.icon(page["icon"])
                                with ui.item_section():
                                    label = ui.label(page_name).style(
                                        "width:120px;"
                                        "opacity:1;"
                                        "transition:opacity .15s ease;"
                                    )
                            self.navigation_items[page_name] = item
                            self.navigation_labels.append(label)
                    ui.space()
                    # Footer
                    with ui.row().classes("w-full h-12 items-center px-5"):
                        ui.icon("info").classes("text-grey")
                        self.navigation_footer = (
                            ui.label("Version 1.0")
                            .classes("text-caption text-grey")
                            .style(
                                "margin-left:16px;opacity:1;transition:opacity .15s ease;"
                            )
                        )


    def toggle(self) -> None:
        self.navigation_expanded = not self.navigation_expanded
        if self.navigation_expanded:
            self.container.style("width:180px; transition:width .25s ease;")
            #self.navigation_title.style("opacity:1; transition:opacity .15s ease;")
            self.navigation_footer.style("opacity:1; transition:opacity .15s ease;")
            for label in self.navigation_labels:
                label.style("opacity:1; transition:opacity .15s ease;")
        else:
            self.container.style("width:60px; transition:width .25s ease;")
            #self.navigation_title.style("opacity:0; transition:opacity .15s ease;")
            self.navigation_footer.style("opacity:0; transition:opacity .15s ease;")
            for label in self.navigation_labels:
                label.style("opacity:0; transition:opacity .15s ease;")


    def select_page(self, page_name) -> None:
        if self.current_page:
            self.navigation_items[self.current_page].classes(remove="bg-blue-200")
        self.current_page = page_name
        self.navigation_items[page_name].classes(add="bg-blue-200")
