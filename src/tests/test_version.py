import madmpy
import madmpy.v1_0.dmp as DMP_1_0
import madmpy.v1_1.dmp as DMP_1_1
import pytest

def test_set_version_inexistent():
    """Tests setting a version that is not supported"""
    with pytest.raises(Exception):
        madmpy.set_version("1.5")
        assert (madmpy.load() == DMP_1_1)

def test_set_version():
    """Testing supported versions"""
    madmpy.set_version("1.0")   # v1.0
    assert (madmpy.load() == DMP_1_0)
    
    madmpy.set_version()        # v1.1
    assert (madmpy.load() == DMP_1_1)