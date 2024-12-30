# madmpy

Validating and creating machine Actionable Data Management Plan descriptions in a pythonic way.

This library attempts to conform to [RDA DMP Common Standard](https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard?tab=readme-ov-file#dmp_modified_tree).

## Quick start

```python
import madmpy as md

dmp = md.read_json("dmp.json")

```
## Exporting DCAT
```python
dmp.dataset[0].to_dcat()
```

## Extending the models
```python
...
```