"""
* Commands: Patreon Integration
"""
import json
import platform
from typing import Annotated

import requests
import typer
from typer import Option

from MPCAutofill.settings import PATREON_CACHE
from cardpicker.constants import SecretKeys
from cardpicker.integrations.patreon import get_patreon_campaign_details, get_patrons
from cardpicker.models import SiteSecret
from cardpicker.schema_types import Patreon, PatreonResponse

app = typer.Typer()

patreon_header = {
    "User-Agent": f"Patreon-Python, version 0.5.1, platform {platform.platform()}",
}


@app.command(
    "update",
    help="Updates current Patreon campaign, tier, and supporter data stored in the database."
)
def update_patreon_data(
    refresh_auth: Annotated[bool, Option(
        "-r", "--refresh-auth",
        help="Also refresh existing Patreon authentication.", show_default=True
    )] = False
) -> None:
    """Pulls the latest Patreon data, and exports it to a JSON file."""
    if refresh_auth:
        authenticate_with_patreon()
    access_token = SiteSecret.get_secret_or_none(SecretKeys.PATREON_ACCESS)
    if not access_token:
        return print("Patreon authentication could not be established.")

    # Get campaign, tiers, and patrons
    campaign, tiers = get_patreon_campaign_details(patreon_access_token=access_token)
    if campaign is None:
        return print("Patreon API did not return a valid campaign.")
    if tiers is None:
        return print("Patreon API did not return a list of valid tiers.")
    members = get_patrons(
        patreon_access_token=access_token,
        campaign_id=campaign.id,
        campaign_tiers=tiers
    ) or []

    # Save Patreon data to JSON file
    with open(PATREON_CACHE, "w") as f:
        json.dump(
            obj=PatreonResponse(
                patreon=Patreon(
                    url=campaign.url,
                    members=members,
                    tiers=tiers,
                    campaign=campaign
                )
            ).model_dump(),
            fp=f, indent=2, sort_keys=True)
    return print(
        "Patreon data updated!\n"
        f"Data saved to: {PATREON_CACHE}")


@app.command(
    "auth",
    help="Used to establish initial authentication with Patreon, or refresh an existing one."
)
def authenticate_with_patreon() -> None:
    """Refreshes authentication with Patreon using provided or existing keys."""

    # Retrieve existing secrets
    patreon_refresh_token = SiteSecret.get_secret_or_none(SecretKeys.PATREON_REFRESH)
    patreon_client_id = SiteSecret.get_secret_or_none(SecretKeys.PATREON_CLIENT)
    patreon_client_secret = SiteSecret.get_secret_or_none(SecretKeys.PATREON_SECRET)

    # Ask for a refresh token?
    if not patreon_refresh_token:
        print("Please enter a valid Patreon REFRESH TOKEN:")
        patreon_refresh_token = input().strip()

    # Ask for a client ID?
    if not patreon_client_id:
        print("Please enter a valid Patreon CLIENT ID:")
        patreon_client_id = input().strip()

    # Ask for a client secret?
    if not patreon_client_secret:
        print("Please enter a valid Patreon CLIENT SECRET:")
        patreon_client_secret = input().strip()

    # Make a request to refresh the Patreon access token
    with requests.post(
        # https://docs.patreon.com/#step-7-keeping-up-to-date
        url="https://www.patreon.com/api/oauth2/token",
        params={
            "grant_type": "refresh_token",
            "refresh_token": patreon_refresh_token,
            "client_id": patreon_client_id,
            "client_secret": patreon_client_secret,
        },
        headers=patreon_header,
    ) as r:

        # Ensure request was successful
        try:
            r.raise_for_status()
            _data = r.json()
        except Exception as e:
            return print(f"Patreon request failed! ({str(e)})")

        # Were the tokens received?
        if "access_token" not in _data or "refresh_token" not in _data:
            return print("Patreon response missing access_token or refresh_token!\n"
                         f"Response: {_data}")

        # Update access and refresh token
        new_access_token = _data.get("access_token", "")
        new_refresh_token = _data.get("refresh_token", "")

        # Insert base keys
        SiteSecret.set_secret(SecretKeys.PATREON_CLIENT, patreon_client_id)
        SiteSecret.set_secret(SecretKeys.PATREON_SECRET, patreon_client_secret)
        SiteSecret.set_secret(SecretKeys.PATREON_ACCESS, new_access_token)
        SiteSecret.set_secret(SecretKeys.PATREON_REFRESH, new_refresh_token)
        return print("Patreon authentication saved!")
