"""
* Command Group: Tags
"""
import json
from typing import Annotated, Optional

from typer import Typer, Argument

from MPCAutofill.settings import CONFIG_DIR
from cardpicker.models import Tag
from cardpicker.schema_types import TagsResponse, Tag as TagSchema, ChildElement as TagChildSchema

# Command group
app = Typer()


"""
* Commands
"""


@app.command("import", help="Import tags from a data file to the database.")
def import_tags(
        data_file: Annotated[
            str, Argument(
                help="Optionally provide the name of a different data file to import tags from. Must be in JSON"
                     "format and adhere to the TagsResponse schema served at the `/tags` endpoint.",
                show_default=True
            )
        ] = "tags.json"
) -> None:
    with open((CONFIG_DIR / data_file), "r", encoding="utf-8") as tags_file:
        tags: TagsResponse = TagsResponse(**json.load(tags_file))

    def _import_tag_group(
            _tag: TagSchema | TagChildSchema,
            parent: Optional[Tag] = None
    ) -> tuple[list[str], list[str]]:
        """Process a tag group, importing its parent followed by children."""
        _tags_created, _tags_updated = [], []
        _obj, _created = Tag.objects.update_or_create(
            name=_tag.name,
            defaults={
                "is_enabled_by_default": _tag.isEnabledByDefault,
                "parent": parent,
                "aliases": _tag.aliases
            })
        if _created:
            _tags_created.append(_tag.name)
        else:
            _tags_updated.append(_tag.name)

        # Create or update children
        for _child in _tag.children:
            _tc, _tu = _import_tag_group(
                _tag=_child,
                parent=_obj)
            _tags_created.extend(_tc)
            _tags_updated.extend(_tu)
        return _tags_created, _tags_updated

    # Import each tag group
    created, updated = [], []
    for tag_group in tags.tags:
        tc, tu = _import_tag_group(
            _tag=tag_group)
        created.extend(tc)
        updated.extend(tu)
    print(f"Tags imported: {', '.join(n for n in created)}")
    print("=" * 120)
    print(f"Tags updated: {', '.join(n for n in updated)}")
