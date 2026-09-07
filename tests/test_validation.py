"""
The official RDA example corpus, against every supported schema version.

Two sets live under `data/rda_dmps/`, and the difference between them is itself a test:
`1.1/` holds the examples as published for schema 1.0/1.1, with identifiers written as
resolver URLs — upstream overwrote these, so it is the only surviving copy — and `1.2/`
holds the current ones, rewritten with bare identifiers, `ex9` also carrying the
1.2-only `project_id`. `data/madmpy_dmps/` holds the one plan of our own.

No `required` field changed between 1.0, 1.1 and 1.2, so every file must validate
against every version except the deviations listed below. Anything else is a regression.

Models are built directly rather than through `validate_DMP` because a `ValidationError`
names the field that failed and a bare `False` does not. `validate_DMP`'s own contract is
checked further down.
"""

import json
from pathlib import Path

import pytest

import madmpy

DATA = Path(__file__).parent.parent / "data"
RDA = DATA / "rda_dmps"
VERSIONS = ["1.0", "1.1", "1.2"]
EXAMPLES = [(corpus, path)
            for corpus in ("1.1", "1.2")
            for path in sorted((RDA / corpus).glob("*.json"))]

# Files that legitimately fail, whatever the version.
KNOWN_DEVIATIONS = {
    ("1.2", "ex10-fairsharing.json"):
        "upstream bug: host.url holds a bare DOI where the schema types a URL "
        "(see RDA-UPSTREAM-ISSUES.md)",
    ("1.1", "ex9-dmp-long.json"):
        "upstream bug: funder_id carries an empty identifier, in a field the schema "
        "makes mandatory (see RDA-UPSTREAM-ISSUES.md). Against v1.2 it also fails on "
        "project_id, which this pre-1.2 file writes as a bare string where schema 1.2 "
        "defines an array of objects",
    ("1.2", "ex9-dmp-long.json"):
        "upstream bug: funder_id carries an empty identifier, in a field the schema "
        "makes mandatory (see RDA-UPSTREAM-ISSUES.md)",
}


def test_both_corpora_are_complete():
    """
    The old suite passed from any working directory because every file resolved as
    "not found". Paths now come from __file__ and the count is asserted.
    """
    assert len(EXAMPLES) == 20, f"found {len(EXAMPLES)} examples under {DATA}"


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("corpus,path", EXAMPLES,
                         ids=[f"{c}-{p.stem.split('-')[0]}" for c, p in EXAMPLES])
def test_official_examples_validate(corpus, path, version):
    deviation = KNOWN_DEVIATIONS.get((corpus, path.name))
    madmpy.set_version(version)
    try:
        madmpy.load().DMP(**json.loads(path.read_text())["dmp"])
    except Exception:
        if deviation:
            pytest.xfail(deviation)
        raise
    assert not deviation, (
        f"{corpus}/{path.name} validates against v{version} now — "
        f"remove it from KNOWN_DEVIATIONS"
    )


# A plan of our own, because the official corpus barely touches what 1.2 added: of the
# eleven fields the version introduced, its ten files use one, `project_id` in ex9. This
# one uses all eleven, and was checked against the published schema with a JSON Schema
# validator before being committed.
MADMPY_1_2 = DATA / "madmpy_dmps" / "all-1_2-fields.json"


def test_the_1_2_fixture_exercises_every_field_the_version_added():
    """
    Guards the fixture itself. If a field is dropped from it the tests below keep
    passing while covering less, which is the one failure a fixture cannot report.
    """
    madmpy.set_version("1.2")
    plan = madmpy.load().DMP(**json.loads(MADMPY_1_2.read_text())["dmp"])
    dataset = plan.dataset[0]

    assert plan.alternate_identifier and plan.related_identifier
    assert dataset.alternate_identifier and dataset.related_identifier
    assert dataset.creator[0].affiliation
    assert dataset.is_reused is True
    assert dataset.rights
    assert dataset.distribution[0].issued
    assert dataset.distribution[0].host.host_id
    assert dataset.technical_resource[0].technical_resource_id
    assert plan.project[0].project_id
    assert plan.contact.affiliation
    # The two fields the schema lets hold either one object or several.
    assert isinstance(plan.contact.contact_id, list)
    assert isinstance(dataset.metadata[0].metadata_standard_id, list)


@pytest.mark.parametrize("version", ["1.0", "1.1"])
def test_the_1_2_fixture_is_rejected_by_the_older_versions(version):
    """It is written in shapes 1.2 introduced, so accepting it would mean those are too lax."""
    madmpy.set_version(version)
    with pytest.raises(Exception):
        madmpy.load().DMP(**json.loads(MADMPY_1_2.read_text())["dmp"])


def dataset_1_2(**extra):
    """A minimal 1.2 dataset, for the fields only that version has."""
    return madmpy.load().Dataset(
        dataset_id={"identifier": "11353/10.923628", "type": "handle"},
        personal_data="no",
        sensitive_data="no",
        title="Dataset",
        **extra,
    )


@pytest.mark.parametrize("given,expected", [
    (True, True),
    (False, False),
    ("yes", True),   # pydantic's lax mode, kept on purpose
    ("no", False),
])
def test_is_reused_is_a_boolean(given, expected):
    """
    `is_reused` is the one field 1.2 typed as a boolean while its five neighbours kept
    yes/no/unknown. The coercion is deliberate: a plan written out of that habit still
    exports as the true/false the schema asks for, instead of being rejected.
    """
    madmpy.set_version("1.2")
    assert dataset_1_2(is_reused=given).is_reused is expected


def test_is_reused_has_no_third_state():
    """1.2 dropped `unknown` for this field, and nothing can be coerced from it."""
    madmpy.set_version("1.2")
    with pytest.raises(Exception):
        dataset_1_2(is_reused="unknown")


def test_is_reused_may_be_omitted():
    """It is not required, and absent must stay absent rather than become False."""
    madmpy.set_version("1.2")
    assert dataset_1_2().is_reused is None
    assert "is_reused" not in dataset_1_2().model_dump(exclude_none=True)


def test_is_reused_false_survives_the_export():
    """
    `export_DMP_json` drops unset fields, and False is a value, not an absence: losing it
    would turn "produced here" into "nobody said". `exclude_none` keeps it; filtering the
    dump on truthiness would not, and that is the refactor this guards against.
    """
    madmpy.set_version("1.2")
    assert dataset_1_2(is_reused=False).model_dump(mode="json",
                                                   exclude_none=True)["is_reused"] is False


def test_the_1_2_fixture_validates_and_re_validates_once_exported():
    madmpy.set_version("1.2")
    module = madmpy.load()
    assert madmpy.validate_DMP(MADMPY_1_2) is True
    plan = module.DMP(**json.loads(MADMPY_1_2.read_text())["dmp"])
    module.DMP(**madmpy.export_DMP_json(plan)["dmp"])


# validate_DMP behaves the same whatever the standard version, so its contract is
# checked against one. Pinned rather than left to chance because the selected version
# is module-level state shared with the other test files.
CONTRACT_VERSION = "1.1"


def test_validate_dmp_reports_a_valid_plan():
    madmpy.set_version(CONTRACT_VERSION)
    assert madmpy.validate_DMP(RDA / "1.1" / "ex8-dmp-minimal-content.json") is True


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("missing", [
    "contact", "created", "dataset", "dmp_id",
    "ethical_issues_exist", "language", "modified", "title",
])
def test_a_plan_missing_a_required_field_is_rejected(version, missing):
    """
    The eight fields the schema lists under `dmp.required`. `ethical_issues_exist`
    used to slip through: it carried a default, so a plan could omit it and still
    validate, and the exported file was then missing a field the standard requires.
    """
    madmpy.set_version(version)
    plan = json.loads((RDA / "1.1" / "ex8-dmp-minimal-content.json").read_text())["dmp"]
    del plan[missing]
    with pytest.raises(Exception):
        madmpy.load().DMP(**plan)


@pytest.mark.parametrize("version", VERSIONS)
def test_a_contributor_may_not_repeat_a_role(version):
    """
    `contributor.role` carries `uniqueItems: true` in all three schemas, and none of
    the models enforced it, so a plan a JSON Schema validator rejects went through.
    """
    madmpy.set_version(version)
    module = madmpy.load()
    contributor = lambda role: module.Contributor(
        name="John Smith",
        role=role,
        contributor_id={"identifier": "https://example.org/person/john-smith",
                        "type": "other"},
    )
    contributor(["DataManager", "Researcher"])
    with pytest.raises(Exception):
        contributor(["DataManager", "DataManager"])


@pytest.mark.parametrize("version", VERSIONS)
def test_a_distribution_must_declare_its_access_mode(version):
    """`data_access` is required by all three schemas; madmpy used to let it be omitted."""
    madmpy.set_version(version)
    with pytest.raises(Exception):
        madmpy.load().Distribution(title="Collection of recordings")


@pytest.mark.parametrize("version,empty_is_valid",
                         [("1.0", False), ("1.1", True), ("1.2", True)])
def test_only_schema_1_0_demands_at_least_one_dataset(version, empty_is_valid):
    """`dmp.dataset` carries minItems 1 in schema 1.0 and nowhere else."""
    madmpy.set_version(version)
    plan = json.loads((RDA / "1.1" / "ex8-dmp-minimal-content.json").read_text())["dmp"]
    plan["dataset"] = []
    if empty_is_valid:
        madmpy.load().DMP(**plan)
    else:
        with pytest.raises(Exception):
            madmpy.load().DMP(**plan)


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("mbox,valid", [
    ("cc@example.com", True),                       # schema 1.1, contact.mbox examples
    ("john.smith@tuwien.ac.at", True),              # data/rda_dmps/1.1/ex9
    ("name.surname@sub.uni-heidelberg.de", True),   # subdomain
    ("", False),
    ("pepe", False),
    ("not an address at all", False),
    ("@@@", False),
    ("a@b", False),                                 # no dot in the domain
])
def test_contact_mbox_must_look_like_an_address(version, mbox, valid):
    """The schema types mbox as `format: email`; madmpy used to accept any string."""
    madmpy.set_version(version)
    module = madmpy.load()
    contact = lambda: module.Contact(
        name="Charlie Chaplin",
        contact_id={"identifier": "0000-0002-1825-0097", "type": "orcid"},
        mbox=mbox,
    )
    if valid:
        contact()
    else:
        with pytest.raises(Exception):
            contact()


@pytest.mark.parametrize("version,extra_keys_allowed",
                         [("1.0", True), ("1.1", False), ("1.2", True)])
def test_only_schema_1_1_closes_the_top_level(version, extra_keys_allowed, tmp_path):
    """
    `additionalProperties: false` appears once in the three schemas, at the top level of
    1.1, and madmpy read `data["dmp"]` without ever looking at the rest. Keys inside the
    plan stay legal everywhere — test_export.py checks those survive the round trip.
    """
    madmpy.set_version(version)
    plan = json.loads((RDA / "1.1" / "ex8-dmp-minimal-content.json").read_text())
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan | {"junk": 1}))

    assert madmpy.validate_DMP(path) is extra_keys_allowed

    # The same file without the extra key validates whatever the version.
    path.write_text(json.dumps(plan))
    assert madmpy.validate_DMP(path) is True


@pytest.mark.parametrize("version,accepted", [("1.0", True), ("1.1", False), ("1.2", True)])
def test_a_1_2_era_file_is_refused_by_1_1_for_its_schema_key(version, accepted):
    """
    The rule above on real files: all ten of `data/rda_dmps/1.2/` carry a top-level `"$schema"`,
    so the same file is valid read as 1.2 and invalid read as 1.1. Pinned because that
    failure looks like a madmpy quirk and a JSON Schema validator does the same.
    """
    madmpy.set_version(version)
    assert madmpy.validate_DMP(RDA / "1.2" / "ex8-dmp-minimal-content.json") is accepted


@pytest.mark.parametrize("contents,reason", [
    (None, "the file does not exist"),
    ("{ not json", "malformed JSON"),
    ('{"foo": 1}', "no top-level dmp key"),
    ('{"dmp": []}', "dmp is not an object"),
    ('{"dmp": {"title": "incomplete"}}', "the plan breaks the schema"),
])
def test_validate_dmp_returns_false_instead_of_raising(tmp_path, contents, reason):
    """
    Every one of these used to be indistinguishable from success: a missing file and a
    valid plan both returned None, and three of them raised out of the function.
    """
    madmpy.set_version(CONTRACT_VERSION)
    path = tmp_path / "plan.json"
    if contents is not None:
        path.write_text(contents)
    assert madmpy.validate_DMP(path) is False, reason
