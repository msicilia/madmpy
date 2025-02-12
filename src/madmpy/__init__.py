import os
from importlib import import_module
from pathlib import Path
from pydantic import ValidationError
import json

DEFAULT_VERSION = "1.1"
_selected_version = None 

def load():
    """
    Returns the DMP class corresponding to the version selected with `set_version()`.

    - If `set_version()` has not been called, the default version is used.
    """
    version = _selected_version or DEFAULT_VERSION
    module_name = f"madmpy.v{version.replace('.', '_')}.dmp"
    module = import_module(module_name)
    return module


def set_version(version: str = None):
    """
    Automatically loads the correct version of DMP.
    - If `version` is `None`, it uses the latest version.
    - If `version` is "1.0", it uses the previous version.
    - If the version is invalid, an error is raised.
    """
    global _selected_version
    _selected_version = version or os.getenv("DMP_VERSION", DEFAULT_VERSION)
    module_name = f"madmpy.v{_selected_version.replace('.', '_')}.dmp"

    try:
        import_module(module_name)
    except ModuleNotFoundError:
        raise ValueError(f"Version {version} not supported.")
    
def validate_DMP(dmp_path):
    """
    Validates a DMP file.
    - Loads the corresponding DMP module.
    - Reads and parses the JSON file at the given path.
    - Validates the DMP instance with Pydantic.
    - Prints a success message if valid; otherwise, prints an error message.
    
    Args:
        dmp_path: Path to the DMP JSON file.
    """ 
    dmp_module = load()

    file = Path(dmp_path).expanduser().resolve()

    if not file.exists():
        print(f"Error: '{file}' not found.")
        return None

    with open(file) as f:  
        data = json.load(f)

    try:
        dmp_instance = dmp_module.DMP(**data["dmp"])
        dmp_module.DMP.model_validate(dmp_instance)
        
        print("DMP validated!")

    except ValidationError as e:
        print("ERROR!", e.errors())

def export_DMP_json(dmp_instance, indent=4):
    """
    Exports a DMP instance as a JSON string.

    Args:
        dmp_instance: A valid DMP object from the loaded module.
        indent: The indentation level for JSON formatting (default is 4).

    Returns:
        str: JSON string with the structure {"dmp": <DMP content>}
    """
    return json.loads(f'{{"dmp": {dmp_instance.model_dump_json(indent=indent)} }}')