import madmpy

dmp_files = [
    "ex1-header-fundedProject.json",
    "ex2-dataset-planned.json",
    "ex3-dataset-finished.json",
    "ex4-dataset-embargo.json",
    "ex5-dataset-planned-host.json",
    "ex6-dataset-closed.json",
    "ex7-dataset-many.json",
    "ex8-dmp-minimal-content.json",
    "ex9-dmp-long.json",
    "ex10-fairsharing.json"
]

def test_validate_DMP():
    """ Testing DMP validation"""
    
    madmpy.set_version("1.1")   # v1.1
    for file in dmp_files:
        madmpy.validate_DMP(f"data/{file}")
    
    madmpy.set_version("1.0")   # v1.0
    for file in dmp_files:
        madmpy.validate_DMP(f"data/{file}")
        
    assert True