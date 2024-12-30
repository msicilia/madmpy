
# Make the imports dependent of the version.
# https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/releases 

def set_version(version: str):
    match version:
        case "1.0":
            from madmpy.v1_0 import Project
        case "1.1":
            from madmpy.v1_1 import Project
        case _:
            raise ValueError(f"Version {version} not supported")
  
from madmpy.v1_1 import DMP

def read_json(file: str):
    """"""
    with open(file) as f:  
        data = json.load(f)
    return DMP.model_validate(data["dmp"])

