from shiny import App, ui

from modules.hello import hello_ui, hello_server
from modules.main import main_ui, main_server

app_ui = ui.page_fluid(
    main_ui("main"),
    hello_ui("hello"),
)


def server(input, output, session):
    main_server("main")
    hello_server("hello")


app = App(app_ui, server)
