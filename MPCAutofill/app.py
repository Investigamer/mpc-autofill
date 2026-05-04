"""
* MPC Autofill Backend CLI
"""
import os

from typer import Typer, Context

import django
from django.core.management import execute_from_command_line

# Boostrap Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MPCAutofill.settings")
django.setup()

from _cli import moxfield, patreon, sources, summarize, dfcs, tags

# CLI entrypoint
autofill_cli = Typer(name="urza")

# Add command groups
autofill_cli.add_typer(
    dfcs.app,
    name="dfcs",
    help="Manage double-faced card data."
)
autofill_cli.add_typer(
    moxfield.app,
    name="moxfield",
    help="Manage Moxfield integration."
)
autofill_cli.add_typer(
    patreon.app,
    name="patreon",
    help="Manage Patreon integration."
)
autofill_cli.add_typer(
    sources.app,
    name="sources",
    help="Manage image sources in the database."
)
autofill_cli.add_typer(
    summarize.app,
    name="summarize",
    help="Summarize information about the database."
)
autofill_cli.add_typer(
    tags.app,
    name="tags",
    help="Manage tags in the database."
)

"""
* Proxy Commands
"""

@autofill_cli.command(
    name="manage",
    no_args_is_help=False,
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
        # Disable Typer's -h/--help for this command
        "help_option_names": []
    }
)
def django_manage(ctx: Context) -> None:
    """Proxy command to Django’s manage.py.

    Usage:
        mpcadmin manage <command> [options]

    Examples:
        - mpcadmin manage collectstatic --noinput
        - mpcadmin manage runserver 0.0.0.0:8000
        - mpcadmin manage migrate --fake
        - mpcadmin manage --help
    """
    # Grab everything after “manage”
    args = list(ctx.args)

    # If no sub-command or user passed -h/--help, show Django’s own help
    if not args or any(arg in ("-h", "--help") for arg in args):
        return execute_from_command_line(["manage.py", "--help"])

    # Otherwise, hand everything off to Django
    return execute_from_command_line(["manage.py"] + args)


if __name__ == "__main__":
    # Invoke CLI
    autofill_cli()
