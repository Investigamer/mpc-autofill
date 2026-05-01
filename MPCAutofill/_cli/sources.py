"""
* Command Group: Sources
"""
import csv
import json
import sys
import time
from pathlib import Path
import re
from typing import Optional, Union, Any, Annotated, Self

from bulk_sync import bulk_sync
from pydantic import BaseModel, model_validator
import tomlkit
from typer import Typer, Argument, Option
import unicodedata
import yaml

from cardpicker.models import Source
from cardpicker.search.search_functions import ping_elasticsearch
from cardpicker.sources.source_types import SourceTypeChoices
from cardpicker.sources.update_database import update_database
from cardpicker.utils import log_hours_minutes_seconds_elapsed
from MPCAutofill.settings import CONFIG_DIR

# Pre-compile patterns
_RE_ALNUM_UNDERSCORE = re.compile(r"[^a-zA-Z0-9_]")
_RE_MULTI_SPACE = re.compile(r" {2,}")

# Map SourceTypeChoices to integer
_SOURCE_TYPE_MAP = {
    "0": SourceTypeChoices.GOOGLE_DRIVE,
    "1": SourceTypeChoices.LOCAL_FILE,
    "2": SourceTypeChoices.AWS_S3
}

# Command group
app = Typer()

"""
* Schemas
"""


class DataFileSource(BaseModel):
    """Represents a Source object imported from or exported to a data file."""
    name: str
    key: str | None = None
    id: str
    ordinal: int | None = None
    type: SourceTypeChoices = SourceTypeChoices.GOOGLE_DRIVE
    description: str = ""
    is_public: bool = True
    is_paused: bool = False

    """Validators"""

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        """Validate the `key` and `type` fields."""
        self.key = self.validate_key(self.key)
        self.type = self.validate_source_type(self.type)
        return self

    def validate_key(self, v: Any) -> str:
        """Checks whether a valid key was provided, if not fallback on `name` field, then normalizes this string
            and return it."""
        if not v or not isinstance(v, str):
            v = self.name

        # Replace any single or concurrent spaces with underscore
        v = _RE_MULTI_SPACE.sub(" ", v.strip()).replace(' ', '_')

        # Strip accents: decompose → drop non-ASCII → reify
        v = unicodedata.normalize('NFKD', v).encode("ascii", "ignore").decode("ascii")

        # Remove any non-underscore, non-alphanumeric characters
        return _RE_ALNUM_UNDERSCORE.sub('', v)

    @staticmethod
    def validate_source_type(v: Any) -> SourceTypeChoices:
        """Interprets a provided number value as a SourceTypeChoices enum."""
        if isinstance(v, SourceTypeChoices):
            return v
        if isinstance(v, str):
            return _SOURCE_TYPE_MAP.get(v, SourceTypeChoices.GOOGLE_DRIVE)
        return SourceTypeChoices.GOOGLE_DRIVE

    """Class Methods"""

    @classmethod
    def get_data_file_source_from_row(cls, row: dict[str, Any]) -> 'DataFileSource':
        """Return a DataFileSource object from a given data file row.

        Args:
            row (dict): A row loaded from a CSV, JSON, YAML, or TOML data file.

        Notes:
            * Ensures backwards compatibility for old 'drives.csv' files that used the now-deprecated
                'drive_id' or 'drive_public' field keys.
            * Enforces the following default field values when missing:
                - type: SourceTypeChoices.GOOGLE_DRIVE
                - description: ""
                - is_public: True
                - is_paused: False
        """
        return cls(
            name=row.get("name"),
            key=row.get("key"),
            id=row.get("id", row.get("drive_id")),
            ordinal=row.get("ordinal"),
            type=row.get("type", row.get("source_type", SourceTypeChoices.GOOGLE_DRIVE)),
            description=row.get("description", ""),
            is_public=row.get("is_public", bool(row.get("drive_public", True))),
            is_paused=row.get("is_paused", False)
        )

    """Utility Methods"""

    def get_db_object(self) -> Optional[Source]:
        """Construct and return a Source object from fields, or None if required data is missing or invalid."""
        if not self.id or not self.name or not self.key:
            # Require a name, key, and identifier
            return None
        return Source(
            key=self.key,
            name=self.name,
            identifier=self.id,
            external_link=None,
            description=self.description,
            ordinal=self.ordinal,
            is_public=self.is_public,
            is_paused=self.is_paused,
            source_type=self.type
        )

    def get_csv_row(self) -> tuple[str, str, str, str, bool, bool]:
        """Returns a Tuple matching the CSV row export format."""
        return (
            self.name,
            self.id,
            self.type,
            self.description,
            self.is_public,
            self.is_paused,
        )

    def get_export_dict(self) -> dict[str, Union[str, bool]]:
        """Returns a Dict matching the JSON, YAML, or TOML export format."""
        return dict(
            name=self.name,
            id=self.id,
            type=self.type,
            description=self.description,
            is_public=self.is_public,
            is_paused=self.is_paused
        )


"""
* Utils: Source Data
"""


def sources_to_data_file_sources() -> list[DataFileSource]:
    """Retrieve a list of rows containing the standardized export format for Source objects."""
    return [
        DataFileSource(
            name=src.name,
            key=src.key,
            id=src.identifier,
            ordinal=src.ordinal or 0,
            description=src.description,
            is_public=src.is_public,
            is_paused=src.is_paused
        ) for src in Source.objects.all()
    ]


"""
* Utils: Read Sources
"""


def read_sources_from_csv(file_path: Path) -> list[dict[str, Any]]:
    """Reads sources from a provided CSV file."""
    with open(file_path, "r", newline="") as f:
        return [n for n in csv.DictReader(f, quotechar='"', quoting=csv.QUOTE_MINIMAL, escapechar='\\')]


def read_sources_from_json(file_path: Path) -> list[dict[str, Any]]:
    """Reads sources from a provided JSON file."""
    with open(file_path, "r") as f:
        return [n for _, n in sorted(json.load(f).items(), key=lambda item: int(item[0]))]


def read_sources_from_yaml(file_path: Path) -> list[dict[str, Any]]:
    """Reads sources from a provided YAML file."""
    with open(file_path, "r") as f:
        return [n for _, n in sorted(yaml.load(f, Loader=yaml.Loader).items(), key=lambda item: int(item[0]))]


def read_sources_from_toml(file_path: Path) -> list[dict[str, Any]]:
    """Reads sources from a provided TOML file."""
    with open(file_path, "r") as f:
        return [n for _, n in sorted(tomlkit.load(f).items(), key=lambda item: int(item[0]))]


def read_sources(file_path: Path) -> list[Source]:
    """Reads sources from a provided data file, according to its file type."""

    # Load raw data from data file
    if file_path.suffix == ".csv":
        _sources = read_sources_from_csv(file_path)
    elif file_path.suffix == ".json":
        _sources = read_sources_from_json(file_path)
    elif file_path.suffix in [".yml", ".yaml"]:
        _sources = read_sources_from_yaml(file_path)
    elif file_path.suffix == ".toml":
        _sources = read_sources_from_toml(file_path)
    else:
        raise NotImplementedError(f"Provided data file type not supported: {file_path.suffix}")

    # Add ordinal based on list order
    sources: list[Source] = []
    for i, row in enumerate(_sources, start=1):
        row["ordinal"] = i
        try:
            _source = DataFileSource.get_data_file_source_from_row(row)
            _source_db_object = _source.get_db_object()
            _source_db_object.pre_save_validation()
            sources.append(_source_db_object)
        except Exception as e:
            print(f"Skipping source at Row {i + 1}! ({str(e)})")
    return sources


"""
* Utils: Write Sources
"""


def write_sources_to_csv(file_path: Path) -> None:
    """Exports sources to a CSV file."""
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_MINIMAL, escapechar='\\')
        writer.writerows([
            ('name', 'id', 'type', 'description', 'is_public', 'is_paused'),
            *[src.get_csv_row() for src in sources_to_data_file_sources()]
        ])


def write_sources_to_json(file_path: Path) -> None:
    """Exports sources to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(
            obj={str(i): n.model_dump() for i, n in enumerate(sources_to_data_file_sources(), start=1)},
            fp=f,
            indent=2
        )


def write_sources_to_yaml(file_path: Path) -> None:
    """Exports sources to a YAML file."""
    with open(file_path, "w") as f:
        yaml.dump(
            data={str(i): n.model_dump() for i, n in enumerate(sources_to_data_file_sources(), start=1)},
            stream=f,
            indent=2
        )


def write_sources_to_toml(file_path: Path) -> None:
    """Exports sources to a TOML file."""
    with open(file_path, "w") as f:
        tomlkit.dump(
            data={str(i): n.model_dump() for i, n in enumerate(sources_to_data_file_sources(), start=1)},
            fp=f
        )


def write_sources(file_path: Path) -> None:
    """Write sources to a provided data file, according to its file type. Returns True if successful."""
    if file_path.suffix == ".csv":
        write_sources_to_csv(file_path)
    elif file_path.suffix == ".json":
        write_sources_to_json(file_path)
    elif file_path.suffix in [".yml", ".yaml"]:
        write_sources_to_yaml(file_path)
    elif file_path.suffix == ".toml":
        write_sources_to_toml(file_path)
    else:
        raise NotImplementedError(
            f"Provided data file type not supported: {file_path.suffix}"
        )


"""
* Import / Export Sources
"""


@app.command(
    "import",
    help="Imports image sources from a provided data file (e.g. drives.csv) to the database.",
    short_help="Import image sources from a provided data file."
)
def import_sources(
        data_file: Annotated[
            str, Argument(
                help="Optionally provide the name of a different data file to import sources from. Supports "
                     "CSV, JSON, YAML, or TOML data files.",
                show_default=True
            )
        ] = "drives.csv"
) -> None:
    """Import drive sources from a provided data file."""
    _path = CONFIG_DIR / data_file
    try:
        # Check if there are any sources to import
        sources = read_sources(_path)
        if sources:
            print(f"Read '{data_file}' file and found {len(sources)} sources.")
            key_fields = ("key",)
            bulk_sync(new_models=sources, key_fields=key_fields, filters=None, db_class=Source)
            return print(f"Sources successfully imported from '{data_file}' file.")
        return print(f"No valid sources were found in '{data_file}' file.")
    except Exception as e:
        print(f"Failed to import sources from '{data_file}' file. ({str(e)})")
        sys.exit(1)


@app.command(
    "export",
    help="Exports image sources from the database to a provided data file (e.g. drives.csv).",
    short_help="Export image sources to a provided data file.",
)
def export_sources(
        data_file: Annotated[
            str, Argument(
                help="Optionally provide the name of a different data file to export sources to. Supports "
                     "CSV, JSON, YAML, or TOML data files.",
                show_default=True
            )
        ] = "drives.csv"
) -> None:
    _path = CONFIG_DIR / data_file
    try:
        # Check if there are sources to export
        _source_count = Source.objects.count()
        if _source_count > 0:
            write_sources(_path)
            _sources = 'source' if _source_count < 2 else 'sources'
            return print(f"{_source_count} {_sources} exported from database to '{data_file}' file.")
        return print("No sources were found in the database to export.")
    except Exception as e:
        print(f"Failed to export sources to '{data_file}' file. ({str(e)})")
        sys.exit(1)


"""
* Update Sources
"""


@app.command(
    "update",
    help="Update all OR a list of specified sources in the database."
)
def update_sources(
        sources: Annotated[Optional[list[str]], Argument(
            help=(
                "Specify one or more of the following sources to update: "
                f"{', '.join(sorted(Source.objects.values_list('key', flat=True)))}"
            )
        )] = None,
        force_update: Annotated[bool, Option(
            "-f", "--force",
            help="Will force drives marked as 'paused' to update, if enabled.",
            show_default=True
        )] = False,
) -> None:
    """Update all OR a list of specified sources in the database."""
    if not ping_elasticsearch():
        raise Exception("Elasticsearch is offline!")
    if not sources:
        sources = None
    t0 = time.time()
    update_database(
        sources=sources,
        is_forced=force_update)
    log_hours_minutes_seconds_elapsed(t0)
