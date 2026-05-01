"""
* Commands: Moxfield Integration
"""
from typing import Annotated

from typer import Argument, Typer

from cardpicker.constants import SecretKeys
from cardpicker.models import SiteSecret

app = Typer()
secret_group = Typer()
app.add_typer(
    secret_group,
    name="secret",
    help="Access or modify the Moxfield secret key."
)

"""
* App Group: Secret
"""


@secret_group.command("get", help="Print the current Moxfield secret key.")
def get_moxfield_secret():
    _secret = SiteSecret.get_secret_or_none(key=SecretKeys.MOXFIELD_SECRET)
    if _secret is None:
        return print("Moxfield secret is not set.")
    return print(_secret)


@secret_group.command("set", help="Set the Moxfield secret key.")
def set_moxfield_secret(value: Annotated[str, Argument(help="Value to set for MOXFIELD_SECRET.")]):
    SiteSecret.set_secret(key=SecretKeys.MOXFIELD_SECRET, value=value)
