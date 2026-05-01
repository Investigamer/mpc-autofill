import platform
from time import sleep
from typing import Optional

import requests

from cardpicker.schema_types import CampaignClass, Supporter, SupporterTier

# Header must be included to access Patreon info
patreon_header = {"User-Agent": f"Patreon-Python, version 0.5.1, platform {platform.platform()}"}


def get_patreon_campaign_details(
    patreon_access_token: str
) -> tuple[Optional[CampaignClass], Optional[dict[str, SupporterTier]]]:
    """
    Get needed patreon campaign details.
    :param patreon_access_token: Patreon access token.
    :return: Campaign ID, list of dictionaries containing supporter tier info.
    """
    try:
        res = requests.get(
            # https://docs.patreon.com/#get-api-oauth2-v2-campaigns
            url="https://www.patreon.com/api/oauth2/v2/campaigns",
            params={
                "include": "tiers",
                "fields[campaign]": ",".join(["summary", "url"]),
                "fields[tier]": ",".join(["title", "description", "amount_cents"]),
            },
            headers={"Authorization": f"Bearer {patreon_access_token}", **patreon_header},
        ).json()

        # Properly format campaign details
        # Todo: Clean up the way we ingest and validate this data
        campaign = CampaignClass(
            id=res["data"][0]["id"],
            about=res["data"][0]["attributes"]["summary"],
            url=res["data"][0]["attributes"]["url"])

        # Properly format campaign tiers
        tiers: dict[str, SupporterTier] = {}
        for tier in res["included"]:
            # Ignore free tier
            if tier["attributes"]["amount_cents"] < 1:
                continue
            # Build dictionary of tiers to reference by ID
            tiers[tier["id"]] = SupporterTier(
                title=tier["attributes"]["title"],
                description=tier["attributes"]["description"],
                usd=round(tier["attributes"]["amount_cents"] / 100),
            )
    except KeyError:
        print("Warning: Cannot locate Patreon campaign. Check Patreon access token!")
        return None, None
    return campaign, tiers


def get_patrons(
    patreon_access_token: str,
    campaign_id: str,
    campaign_tiers: dict[str, SupporterTier],
    page: Optional[str] = None
) -> Optional[list[Supporter]]:
    """
    Get our patreon contributors.
    :note: https://docs.patreon.com/#get-api-oauth2-v2-campaigns-campaign_id-members
    :return: List of dictionaries containing patreon contributor info.
    """
    headers = {"Authorization": f"Bearer {patreon_access_token}", **patreon_header}
    try:
        # Use page if provided, otherwise build a complete query
        res = (
            requests.get(
                url=page,
                headers=headers
            ).json() if page else requests.get(
                url=f"https://www.patreon.com/api/oauth2/v2/campaigns/{campaign_id}/members",
                params={
                    "include": "currently_entitled_tiers",
                    "fields[member]": ",".join(
                        ["full_name", "campaign_lifetime_support_cents", "pledge_relationship_start", "patron_status"]
                    ),
                },
                headers=headers,
            ).json()
        )

        # Return formatted list of patrons
        results: list[Supporter] = []
        for mem in res.get("data", []):

            # Skip non-active members
            mem_details = mem.get("attributes", {})
            if mem_details.get("patron_status") != "active_patron":
                continue

            # Pull subscribed tiers for this member
            mem_tiers = [
                campaign_tiers[t["id"]]
                for t in mem.get("relationships", {}).get("currently_entitled_tiers", {}).get("data", [])
                if t.get("id") in campaign_tiers
            ]

            # Skip members with no subscribed tiers
            if not mem_tiers:
                continue

            # Use member's highest subscribed tier
            current_tier = sorted(mem_tiers, key=lambda item: item.usd)[0]

            # Add member to results
            results.append(
                Supporter(
                    name=mem_details.get("full_name", "Unknown"),
                    tier=current_tier.title or "Unknown Tier",
                    date=mem_details.get("pledge_relationship_start", "2024-01-01")[:10],
                    usd=current_tier.usd or 5,
                )
            )

        # Check for additional page results
        next_page = res.get("links", {}).get("next")
        if next_page:
            # Rate limit additional page requests
            sleep(.5)
            results.extend(
                get_patrons(
                    patreon_access_token=patreon_access_token,
                    campaign_id=campaign_id,
                    campaign_tiers=campaign_tiers,
                    page=next_page
                ) or [])

        # Return sorted results at top-level
        if page:
            return results
        return sorted(results, key=lambda item: item.usd, reverse=True)

    # Unable to retrieve patrons
    except KeyError:
        print("Warning: Cannot locate Patreon campaign. Check Patreon access token!")
        return None


__all__ = ["get_patreon_campaign_details", "get_patrons"]
