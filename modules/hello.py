from shiny import module, ui, render


@module.ui
def hello_ui():
    return ui.card(
        ui.card_header("Hello"),
        ui.output_text("hello_text"),
    )


@module.server
def hello_server(input, output, session):
    @render.text
    def hello_text():
        return "Hello from the hello module."
