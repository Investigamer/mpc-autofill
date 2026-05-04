from typing import Any

import typer

from django.core.management.base import BaseCommand
from django.db.models import Sum

from cardpicker.models import Card, CardTypes

# Command group
app = typer.Typer()


"""
* Utils
"""


class ByteFactor:
    KB = 1000
    MB = KB * KB
    GB = MB * KB
    TB = GB * KB
    PB = TB * KB


def size_to_human_readable(size: int) -> str:
    """Convert a size integer in bytes to a human-readable string using the nearest form factor (MB, GB, TB, etc.)

    Args:
        size (int): Size in bytes.

    Returns:
        str: Size as a human-readable string, e.g. 100 MB.
    """
    if size >= ByteFactor.PB:
        return f"{size / ByteFactor.PB:2f} PB"
    elif size >= ByteFactor.TB:
        return f"{size / ByteFactor.TB:2f} TB"
    elif size >= ByteFactor.GB:
        return f"{size / ByteFactor.GB:2f} GB"
    elif size >= ByteFactor.MB:
        return f"{size / ByteFactor.MB:2f} MB"
    return f"{size / ByteFactor.KB:2f} KB"


@app.command(
    "size",
    help="Summarize the total combined file size of all cards in the database, broken down by card type.",
    short_help="Summarize the total file size of all cards in the database."
)
def image_file_size():
    """Returns the total size of all images in the database"""
    card_size = Card.objects.filter(card_type=CardTypes.CARD).aggregate(Sum("size"))["size__sum"]
    cardback_size = Card.objects.filter(card_type=CardTypes.CARDBACK).aggregate(Sum("size"))["size__sum"]
    token_size = Card.objects.filter(card_type=CardTypes.TOKEN).aggregate(Sum("size"))["size__sum"]
    print(
        f"Total size: {size_to_human_readable((card_size + cardback_size + token_size))} - "
        f"cards: {size_to_human_readable(card_size)}, "
        f"cardbacks: {size_to_human_readable(cardback_size)}, "
        f"tokens: {size_to_human_readable(token_size)}"
    )
