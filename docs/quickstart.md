# Quickstart

Welcome to `madmpy`, a Python library designed to help manage and validate Data Management Plans (DMPs). This guide will walk you through installing `madmpy`, setting up your first project, and running basic operations.

## Installation

Ensure you have Python 3.11+ installed, then install `madmpy` (preferably in a `virtualenv`) using `pip` as follows:

```bash
$ pip install madmpy
```

Alternatively, install from the source:

```bash
git clone https://github.com/msicilia/madmpy.git
cd madmpy
pip install -e .
```

!!! warning
    If you encounter issues during installation, ensure that you have the required dependencies installed. You may need: `pip install 'pydantic>=2.10.4'`

## Using madmpy

Once installed, you can start using `madmpy`. The following sections demonstrate its basic functionality.

### Import the library

First, import `madmpy` into your Python script or interactive session:

``` python
import madmpy
```

To work with DMPs, load the module after importing `madmpy`:

```python
>>> import madmpy
>>> dmp_module = madmpy.load()
Loaded madmpy with RDA-DMP specification v1.1
```

!!! note
    `madmpy` by default uses the latest version of the [RDA-DMP Common Standard](https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/releases), currently `1.1`. To use an older version, specify it explicitly using `set_version(VERSION)`.
    
    ```python
    >>> import madmpy
    >>> VERSION = "1.0"
    >>> madmpy.set_version(VERSION)
    >>> dmp_module = madmpy.load()
    Loaded madmpy with RDA-DMP specification v1.0
    ```

### Validate a DMP file

To validate a DMP file in `JSON` format, provide the file path to `validate_DMP(path/to/file)`.

``` python
>>> madmpy.validate_DMP("data/ex9-dmp-long.json")
DMP validated!
```

You can use example files provided by the [Research Data Alliance](https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/tree/master/examples/JSON), located in the `data` folder of the project.

### Create a DMP

Besides validating DMPs under the RDA-DMP Common Standard, `madmpy` allows creating new DMPs that conform to this specification.

Following the [API Reference](dmp.md), you can create objects corresponding to the DMP. Below is an example of a `.py` snippet to generate a DMP including only the required components.

```python
import madmpy

dmp_module = madmpy.load()

title = "DMP Title"
language = dmp_module.LanguageEnum.eng
dataset = dmp_module.Dataset(
    dataset_id=dmp_module.DatasetIdentifier(
        identifier="https://doi.org/10.25504/FAIRsharing.r3vtvx",
        type=dmp_module.dmp_dataset_id_type.DOI,
    ),
    description="Dataset description example",
    personal_data="no",
    sensitive_data="no",
    technical_resource=[dmp_module.TechnicalResource(name="Technical resource")],
    title="Dataset title",
)

contact = dmp_module.Contact(
    name="name",
    contact_id=dmp_module.ContactIdentifier(
        identifier="https://orcid.org/0000-0001-2345-6789",
        type=dmp_module.contact_id_type.ORCID,
    ),
    mbox="name@email.com",
)

dmp_id = dmp_module.DMPIdentifier(
    identifier="https://doi.org/10.15497/rda00039", 
    type=dmp_module.dmp_dataset_id_type.DOI)

DMP = dmp_module.DMP(
    dataset=[dataset], 
    language=language, 
    title=title, 
    contact=contact,
    dmp_id=dmp_id,
    ethical_issues_exist=dmp_module.YesNoUnknown.NO,
    created= datetime.datetime.now().replace(microsecond=0),
    modified= datetime.datetime.now().replace(microsecond=0),
)
```

This will generate a `DMP` object based on Pydantic, which internally handles validations and constraints of the standard. To convert this object to JSON, use Pydantic's [`model_dump_json()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json) method:

```python
print(DMP.model_dump_json(indent=4))
```

This will generate a JSON-formatted representation that can be stored or used for validation.

``` json
{
    "title": "DMP Title",
    "contact": {
        "name": "name",
        "contact_id": {
            "identifier": "https://orcid.org/0000-0001-2345-6789",
            "type": "orcid"
        },
        "mbox": "name@email.com"
    },
    "contributor": null,
    "cost": null,
    "created": "2025-02-10T13:49:29",
    "dataset": [
        {
            "data_quality_assurance": null,
            "dataset_id": {
                "identifier": "https://doi.org/10.25504/FAIRsharing.r3vtvx",
                "type": "doi"
            },
            "description": "Dataset description example",
            "distribution": null,
            "issued": null,
            "keyword": null,
            "language": null,
            "metadata": null,
            "personal_data": "no",
            "preservation_statement": null,
            "security_and_privacy": null,
            "sensitive_data": "no",
            "technical_resource": [
                {
                    "description": null,
                    "name": "Technical resource"
                }
            ],
            "title": "Dataset title",
            "type": null
        }
    ],
    "description": null,
    "dmp_id": null,
    "ethical_issues_description": null,
    "ethical_issues_exist": "no",
    "ethical_issues_report": null,
    "language": "eng",
    "modified": "2025-02-10T13:49:29",
    "project": null
}
```

!!! note
    Autocompletion in Visual Studio Code (VS Code) may not work correctly because the DMP version is loaded dynamically when initializing the library. To learn about the parameters of each standard component, refer to the [API Reference](dmp.md).

Now you're ready to start working with `madmpy`! 🚀
