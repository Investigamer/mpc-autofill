from dataclasses import dataclass
import pycountry

DATE_FORMAT = "jS F, Y"
DEFAULT_LANGUAGE = pycountry.languages.get(alpha_2="EN")

NEW_CARDS_PAGE_SIZE = 12
NEW_CARDS_DAYS = 14
EDITOR_SEARCH_MAX_QUERIES = 300
CARDS_PAGE_SIZE = 1000
EXPLORE_SEARCH_MAX_PAGE_SIZE = 100

MAX_SIZE_MB = 30
NSFW = "NSFW"

@dataclass
class SecretKeys:
    """Recognized secret keys."""

    # Moxfield Integration
    MOXFIELD_SECRET = "MOXFIELD.SECRET"

    # Patreon Integration
    PATREON_ACCESS = "PATREON.ACCESS"
    PATREON_REFRESH = "PATREON.REFRESH"
    PATREON_CLIENT = "PATREON.CLIENT"
    PATREON_SECRET = "PATREON.SECRET"
