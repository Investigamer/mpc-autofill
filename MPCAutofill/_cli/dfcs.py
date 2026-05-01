from typer import Typer

from cardpicker.dfc_pairs import sync_dfcs

app = Typer()


@app.command(
    "update",
    help="Synchronises stored double-faced card pairs with current Scryfall data.",
)
def update_dfcs():
    sync_dfcs()
