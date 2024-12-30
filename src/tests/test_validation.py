from madmpy import set_version, DMP
import pytest 
from pathlib import Path
import json
from pydantic_core import from_json 


def test_set_global_version():
    set_version("1.1")
    assert True

def test_set_global_version_inexistent():
    """Tests setting a version that is not supported"""
    with pytest.raises(Exception):
        set_version("1.5")

def test_read_dmp():
    file = Path(__file__).parent / Path("data/ex10-fairsharing.json")  
    with open(file) as f:  
        data = json.load(f)
    dmp = DMP.model_validate(data["dmp"])
    print(dmp.dataset[0].to_dcat())
    assert True


