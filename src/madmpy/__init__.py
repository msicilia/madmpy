from importlib import import_module
from pathlib import Path
from pydantic import ValidationError
import json

DEFAULT_VERSION = "1.2"
_selected_version = None


def _module_for(version):
    """The import path of a spec version's models. The single place that mapping lives."""
    return f"madmpy.v{version.replace('.', '_')}.dmp"


def load():
    """
    Returns the module holding the models of the version selected with `set_version()`.

    - If `set_version()` has not been called, `DEFAULT_VERSION` is used.
    """
    return import_module(_module_for(_selected_version or DEFAULT_VERSION))


def set_version(version: str = None):
    """
    Selects the version of the RDA-DMP Common Standard to validate against.

    - If `version` is `None`, `DEFAULT_VERSION` is used.
    - If the version is not supported, `ValueError` is raised and the previously
      selected version stays in force.

    Args:
        version: The spec version, such as "1.0", "1.1" or "1.2".

    Raises:
        ValueError: If no models ship for that version.
    """
    global _selected_version
    requested = version or DEFAULT_VERSION

    try:
        import_module(_module_for(requested))
    except ModuleNotFoundError as error:
        # A dependency missing inside a version's models raises this too; only an
        # unknown version becomes a ValueError.
        if error.name and not error.name.startswith("madmpy.v"):
            raise
        raise ValueError(f"Version {requested} not supported.") from None

    # Assigned only after a successful import, so a failed call changes nothing.
    _selected_version = requested


def validate_DMP(dmp_path):
    """
    Validates a DMP file against the selected version of the standard.

    Reports what it found on stdout and returns the verdict. Nothing raises: a missing
    or unreadable file, malformed JSON, no top-level `dmp` key, another top-level key
    where the version forbids one, and a plan that breaks the schema all print an error
    and return `False`.

    Args:
        dmp_path: Path to the DMP JSON file.

    Returns:
        bool: True if the file holds a valid DMP, False otherwise.
    """
    dmp_module = load()

    file = Path(dmp_path).expanduser().resolve()

    if not file.exists():
        print(f"Error: '{file}' not found.")
        return False

    try:
        with open(file) as f:
            data = json.load(f)
    except json.JSONDecodeError as error:
        print(f"Error: '{file}' is not valid JSON: {error}")
        return False
    except OSError as error:
        print(f"Error: '{file}' could not be read: {error}")
        return False

    # Every maDMP is wrapped in a top-level "dmp" key.
    if not isinstance(data, dict) or not isinstance(data.get("dmp"), dict):
        print(f"Error: '{file}' has no top-level 'dmp' object.")
        return False

    # Only schema 1.1 closes the top level, so the rule travels with the models.
    if not dmp_module.ALLOWS_EXTRA_ROOT_KEYS and set(data) != {"dmp"}:
        others = sorted(set(data) - {"dmp"})
        print(f"Error: '{file}' has {others} at the top level, where this version "
              f"of the standard admits only 'dmp'.")
        return False

    try:
        dmp_module.DMP(**data["dmp"])
    except ValidationError as e:
        print("ERROR!", e.errors())
        return False

    print("DMP validated!")
    return True


def export_DMP_json(dmp_instance):
    """
    Exports a DMP instance as the JSON structure the standard expects.

    Unset fields are omitted rather than written as `null`.

    Args:
        dmp_instance: A valid DMP object from the loaded module.

    Returns:
        dict: The plan wrapped as {"dmp": <DMP content>}.
    """
    return {"dmp": dmp_instance.model_dump(mode="json", exclude_none=True)}