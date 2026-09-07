
## Release Notes

### 0.2.0

* **Support for version 1.2 of the RDA-DMP Common Standard, now the default.** `1.1` and
  `1.0` remain available through `set_version()`.
* New objects in `v1_2`: affiliations, creators, alternate and related identifiers, and
  identifiers for hosts, projects and technical resources.
* In schema 1.2 every identifier `type` is free text with suggested values, except
  `MetadataIdentifier.type`, which still admits only `url` or `other`. The enums are kept
  as a convenience but no longer restrict what a plan may say.
* `Contact.contact_id`, `Contributor.contributor_id`, `Creator.creator_id` and
  `Metadata.metadata_standard_id` accept either one identifier or a list of them.
* `validate_DMP()` returns `True` or `False` instead of returning nothing, and no longer
  raises on a missing file, unreadable file, malformed JSON or a missing `dmp` key.
* `export_DMP_json()` returns a dictionary and omits unset fields rather than writing
  them as `null`.
* Identifiers are validated in every field that carries one, against patterns pinned to
  their specifications. `mbox` is validated as an email address.
* ROR identifiers are checked in `v1_2`, check digits included.
* `ethical_issues_exist` and `distribution.data_access` are now required. Five date
  fields moved from `datetime` to `date`.
* `contributor.role` no longer accepts the same role twice.
* Under version `1.1`, a file carrying a key next to the top-level `dmp` is refused.
  This makes the RDA's own 1.2-era examples invalid when read as `1.1`, since they
  declare a `$schema` key. Keys *inside* `dmp` stay valid in every version.
* The examples now build `created` and `modified` with a timezone, so the plan they
  produce carries a valid RFC 3339 `date-time`.
* Fields the standard does not define survive a load and export round trip instead of
  being silently dropped.
* The `DMP_VERSION` environment variable no longer changes the selected version.

### 0.1.0

* Initial release