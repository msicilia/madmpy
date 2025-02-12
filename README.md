# madmpy

Validating and creating machine Actionable Data Management Plan descriptions in a pythonic way.

**madmpy** is a Python library for creating and validating Data Management Plans (DMPs) following the recommendations of the [RDA DMP Common Standard](https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard).


## Installation
Ensure you have Python **3.11+** installed. You can install `madmpy` using `pip`:

```sh
pip install madmpy
```

## Quickstart
Import the library in your Python script or interactive session:

```python
import madmpy
```

To load the DMP module:

```python
>>> import madmpy
>>> dmp_module = madmpy.load()
Loaded madmpy with RDA-DMP specification v1.1
```

To use an older version of the RDA-DMP Common Standard:

```python
>>> import madmpy
>>> VERSION = "1.0"
>>> madmpy.set_version(VERSION)
>>> dmp_module = madmpy.load()
Loaded madmpy with RDA-DMP specification v1.0
```

### Validate a DMP File
To validate a DMP file in JSON format:

```python
>>> madmpy.validate_DMP("path_DMP_JSON")
DMP validated!
```


### Create a DMP
You can generate a new DMP that conforms to the RDA-DMP Common Standard using `madmpy`. Below is an example with only the required elements:

```python
import datetime
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
    created=datetime.datetime.now().replace(microsecond=0),
    modified=datetime.datetime.now().replace(microsecond=0),
)
```

### Convert to JSON
To generate a JSON representation of the DMP object:

```python
madmpy.export_DMP_json(DMP)
```

This will output a structured JSON-formatted representation of the DMP:

```json
{
    "dmp": {
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
        "created": "2025-02-12T08:15:03",
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
        "dmp_id": {
            "identifier": "https://n2t.net/ark:/123456/xyz123?info",
            "type": "ark"
        },
        "ethical_issues_description": null,
        "ethical_issues_exist": "no",
        "ethical_issues_report": null,
        "language": "eng",
        "modified": "2025-02-12T08:15:03",
        "project": null
    }
}
```

## Contributing
Contributions are welcome! If you would like to improve `madmpy`, follow these steps:

1. **Fork the repository**
2. **Create a new branch** for your feature or fix
3. **Commit your changes** and write meaningful commit messages
4. **Push your branch** to your fork
5. **Submit a Pull Request (PR)**

### Issues & Feature Requests
- If you find a bug or have a feature request, [open an issue](https://github.com/msicilia/madmpy/issues).

## License
This project is licensed under the **MIT License**.

## 📖 Documentation
For a detailed API reference and more examples, check out the [official documentation](https://madmpy.readthedocs.io/).