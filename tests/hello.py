from nicegui import ui


@ui.page("/")
def home():
    print("HOME")
    ui.label("Helllo")


ui.run()