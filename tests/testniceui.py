from nicegui import ui


@ui.page("/")
def home():
    print("HOME")

    ui.label("Hello")


ui.run(reload=True)