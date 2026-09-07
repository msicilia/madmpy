# madmpy API Reference v1.2

Welcome to the `madmpy` API Reference. This documentation provides a comprehensive overview of the available modules, classes, and methods within the library. The `madmpy` library is designed to facilitate the creation, validation, and management of Data Management Plans (DMPs) based on the [RDA-DMP Common Standard](https://www.rd-alliance.org/groups/dmp-common-standards-wg/outputs/). Whether you are integrating DMP functionalities into your system or exploring the different components of a DMP, this reference will help you understand and use the structures and parameters effectively.

!!! note
    Version 1.2 leaves identifier `type` fields as free text, with suggested values given in each field's description. `MetadataIdentifier.type` is the one exception and still admits only `url` or `other`. The enums in this module are kept as a convenience — `dmp_module.contact_id_type.ORCID` still works — but they no longer restrict what a plan may say.

::: src.madmpy.v1_2.dmp
