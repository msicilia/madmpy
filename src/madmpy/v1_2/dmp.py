from pydantic import BaseModel, ConfigDict, AfterValidator, AnyUrl, Field, ValidationError
from enum import Enum
from datetime import date, datetime
from typing import Optional, Union
from typing_extensions import Annotated
import re

from ..languages import LanguageEnum
from ..currency_code import CurrencyCode
from ..country_code import CountryCode

# Schema 1.2 sets no additionalProperties, so a file may carry other top-level keys
# next to "dmp". The ten official examples all use one, $schema.
ALLOWS_EXTRA_ROOT_KEYS = True

def extract_identifier(url, id_type):
    """
    Extracts the identifier from a URL based on the specified type.

    Args:
        url (str): The URL containing the identifier.
        id_type (str): The type of identifier to extract. Supported types are "doi", "orcid", "ark", "ror" and "handle".

    Returns:
        str or None: The extracted identifier if found, otherwise None. Handles are
            returned bare, stripped of the resolver URL when they carry one.
    """
    patterns = {
        "doi": r"10\.\d{4,9}/[-._;()/:A-Z0-9]+$",
        "orcid": r"\d{4}-\d{4}-\d{4}-\d{3}[0-9X]{1}$",
        "ark": r"ark:\/?\S+$",
        "ror": r"0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}$",
    }

    # A handle's local name may contain slashes (RFC 3651, sec. 2), so it cannot be
    # scraped: strip the resolver or DSpace prefix instead, or assume it is already bare.
    if id_type == "handle":
        for resolver in (r"^https?://(?:hdl\.)?handle\.net/(.+)$",
                         r"^https?://\S*?/handle/(.+)$"):
            match = re.match(resolver, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return url

    if id_type not in patterns:
        return url

    match = re.search(patterns[id_type], url, re.IGNORECASE)
    return match.group(0) if match else None

def ror_checksum(identifier):
    """
    The two check digits a ROR ID has to end in.

    ISO/IEC 7064 mod 97-10 over the first seven characters, read as one base 32 Crockford
    number. That encoding is why the alphabet skips i, l, o and u.

    Args:
        identifier (str): A bare ROR ID, such as "03yrm5c26".

    Returns:
        str: The two digits, zero padded.
    """
    alphabet = "0123456789abcdefghjkmnpqrstvwxyz"
    number = 0
    for character in identifier[:7]:
        number = number * 32 + alphabet.index(character)

    return f"{98 - (number * 100) % 97:02d}"

def validate_id(value):
    """
    Validates an identifier, or a list of identifiers.

    Args:
        value (object): An object with `type` and `identifier` attributes, or a list of
            them, which is the form schema 1.2 admits for several identifier fields.

    Raises:
        ValueError: If the object does not have `type` and `identifier` attributes.
        ValueError: If the identifier does not match the expected format for its type.

    Returns:
        object: The validated `value` object.
    """
    if isinstance(value, list):
        for item in value:
            validate_id(item)
        return value

    if not hasattr(value, "type") or not hasattr(value, "identifier"):
        raise ValueError("The object must have 'type' and 'identifier' attributes.")

    identifier = extract_identifier(str(value.identifier).strip(), value.type)
    if not identifier:
        raise ValueError(f"No valid {value.type} identifier found in URL.")

    match value.type:
        case "doi":
            doi_pattern = r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$"
            if not re.match(doi_pattern, identifier, re.IGNORECASE):
                raise ValueError("Invalid DOI format")
        case "orcid":
            orcid_pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]{1}$"
            if not re.match(orcid_pattern, identifier):
                raise ValueError("Invalid ORCID format")
        case "ark":
            # Both labels stay valid: current "ark:NAAN/" and legacy "ark:/NAAN/" (ARK
            # spec 2.2). NAANs are betanumeric (2.3); the name takes subparts, variants
            # and inflections (2.5, 5.2).
            ark_pattern = r"^ark:\/?[bcdfghjkmnpqrstvwxz0-9]+\/[A-Za-z0-9=~*+@_$.\/-]+(\?\S*)?$"
            if not re.match(ark_pattern, identifier):
                raise ValueError("Invalid ARK format")
        case "handle":
            # The global registry only assigns numeric prefixes. RFC 3651 allows
            # non-numeric ones; rejecting those is deliberate.
            handle_pattern = r"^\d+(\.\d+)*\/\S+$"
            if not re.match(handle_pattern, identifier):
                raise ValueError("Invalid Handle format")
        case "url":
            # Same notion of URL the models use for host.url and download_url.
            try:
                AnyUrl(identifier)
            except ValidationError:
                raise ValueError("Invalid URL format")
        case "isni":
            # 15 digits and a check character that may be X, optionally grouped
            # (ISO 27729).
            isni_pattern = r"^\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{3}[\dX]$"
            if not re.match(isni_pattern, identifier):
                raise ValueError("Invalid ISNI format")
        case "ror":
            # A zero, six characters in base 32 Crockford and two check digits
            # (ISO/IEC 7064).
            ror_pattern = r"^0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}$"
            if not re.match(ror_pattern, identifier):
                raise ValueError("Invalid ROR format")
            if ror_checksum(identifier) != identifier[-2:]:
                raise ValueError("Invalid ROR check digits")
        case _:
            # Schema 1.2 turned every identifier type but the metadata standard's into
            # free text, so an unrecognised one is legal here and the emptiness check
            # above is all that can be asserted. In 1.0 and 1.1 this branch raises.
            pass

    return value

def validate_email(value):
    """
    Validates an email address.

    A pragmatic check for `format: email`, not an RFC 5322 parser. A domain with no dot
    is rejected too.

    Args:
        value (str): The address to validate.

    Raises:
        ValueError: If the value does not look like an email address.

    Returns:
        str: The validated address.
    """
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        raise ValueError("Invalid email format")

    return value


def validate_unique(value):
    """
    Rejects a list with repeated entries.

    Args:
        value (list): The list to check.

    Raises:
        ValueError: If any entry appears more than once.

    Returns:
        list: The validated list.
    """
    if len(value) != len(set(value)):
        raise ValueError("Duplicate entries are not allowed")

    return value


class metadata_id_type(str, Enum):
    """
    Enum for allowed metadata identifier types. The only identifier type schema 1.2 still
    closes to a fixed list.

    Args:
        URL: Identifier type is a URL.
        OTHER: Other unspecified identifier type.
    """
    URL = "url"
    OTHER = "other"

class contact_id_type(str, Enum):
    """
    Suggested contact identifier types. Schema 1.2 takes any string here, so this enum is
    a convenience rather than a constraint.

    Args:
        ORCID (str): Open Researcher and Contributor ID.
        ISNI (str): International Standard Name Identifier.
        OPENID (str): OpenID for user authentication.
        OTHER (str): Other unspecified identifier type.
    """
    ORCID = "orcid"
    ISNI = "isni"
    OPENID = "openid"
    OTHER = "other"

class contributor_id_type(str, Enum):
    """
    Suggested contributor identifier types. Schema 1.2 takes any string here, so this enum
    is a convenience rather than a constraint.

    Args:
        ORCID (str): Open Researcher and Contributor ID.
        ISNI (str): International Standard Name Identifier.
        OPENID (str): OpenID for user authentication.
        OTHER (str): Other unspecified identifier type.
    """
    ORCID = "orcid"
    ISNI = "isni"
    OPENID = "openid"
    OTHER = "other"

class creator_id_type(str, Enum):
    """
    Suggested creator identifier types. Schema 1.2 takes any string here, so this enum is
    a convenience rather than a constraint.

    Args:
        ORCID (str): Open Researcher and Contributor ID.
        ISNI (str): International Standard Name Identifier.
        OPENID (str): OpenID for user authentication.
    """
    ORCID = "orcid"
    ISNI = "isni"
    OPENID = "openid"

class affiliation_id_type(str, Enum):
    """
    Suggested affiliation identifier types. Schema 1.2 takes any string here, so this enum
    is a convenience rather than a constraint.

    Args:
        ROR (str): Research Organization Registry identifier.
        GRID (str): Global Research Identifier Database identifier.
        ISNI (str): International Standard Name Identifier.
        OTHER (str): Other unspecified identifier type.
    """
    ROR = "ror"
    GRID = "grid"
    ISNI = "isni"
    OTHER = "other"

class project_id_type(str, Enum):
    """
    Suggested project identifier types. Schema 1.2 takes any string here, so this enum is
    a convenience rather than a constraint.

    Args:
        DOI (str): Digital Object Identifier.
        RAID (str): Research Activity Identifier.
        URL (str): A direct URL to the project.
    """
    DOI = "doi"
    RAID = "raid"
    URL = "url"

class _MaDMPModel(BaseModel):
    """
    Base for every model in this module.
    """
    model_config = ConfigDict(extra="allow")

class AffiliationIdentifier(_MaDMPModel):
    """
    Represents an identifier for an affiliation.

    Args:
        identifier (str): A unique identifier for the organisation. Example: "03yrm5c26".
        type (str): The type of identifier. Suggested values: ror, grid, isni, other.
    """
    identifier: str
    type: str

class Affiliation(_MaDMPModel):
    """
    Represents an organisation a person is affiliated with.

    Args:
        affiliation_id (AffiliationIdentifier): The identifier of the organisation.
        name (str): The name of the organisation. Example: "Some University".
    """
    affiliation_id: Annotated[AffiliationIdentifier, AfterValidator(validate_id)]
    name: str

class AlternateIdentifier(_MaDMPModel):
    """
    Represents an alternate identifier of a DMP or a dataset.

    Args:
        identifier (str): The identifier value. Example: "E-GEOD-34814".
        type (str): The type of alternate identifier. Example: "accession number".
    """
    identifier: str
    type: str

class RelatedIdentifier(_MaDMPModel):
    """
    Represents a resource related to a DMP or a dataset.

    Args:
        identifier (str): The identifier of the related resource. Example: "https://example.com/".
        metadata_scheme (str): Name of the related metadata schema, if applicable. Example: "DDI-L".
        relation_type (str): How this resource relates to the related one, from DataCite's relationType. Example: "HasMetadata".
        resource_type (str): The type of the related resource, from DataCite's resourceTypeGeneral. Example: "Model".
        scheme_type (str): The type of the metadata scheme linked with scheme_uri, if applicable. Example: "XSD".
        scheme_uri (AnyUrl): Link to the scheme of the identifier, if applicable.
        type (str): The type of the identifier, from DataCite's relatedIdentifierType. Example: "url".
    """
    identifier: str
    metadata_scheme: Optional[str] = None
    relation_type: str
    resource_type: Optional[str] = None
    scheme_type: Optional[str] = None
    scheme_uri: Optional[AnyUrl] = None
    type: str

class ContactIdentifier(_MaDMPModel):
    """
    Represents a unique identifier for the contact person in a DMP.

    Args:
        identifier (str): A unique identifier for the contact, such as an ORCID. Example: "0000-0003-0644-4174".
        type (str): The type of identifier. Suggested values: orcid, isni, openid.
    """
    identifier: str
    type: str

class Contact(_MaDMPModel):
    """
    Represents the main contact person for a DMP.

    Args:
        affiliation (List[Affiliation]): The organisations the contact belongs to.
        contact_id (ContactIdentifier): The identifier of the contact, or a list of them.
        mbox (str): The contact person's email address, validated as such. Example: "cc@example.com".
        name (str): The name of the contact person. Example: "Charlie Chaplin".
    """
    affiliation: Optional[list[Affiliation]] = None
    contact_id: Annotated[
        Union[ContactIdentifier, Annotated[list[ContactIdentifier], Field(min_length=1)]],
        AfterValidator(validate_id),
    ]
    mbox: Annotated[str, AfterValidator(validate_email)]
    name: str

class dmp_dataset_id_type(str, Enum):
    """
    Suggested DMP and dataset identifier types. Schema 1.2 takes any string here, so this
    enum is a convenience rather than a constraint.

    Args:
        HANDLE: Handle.
        DOI: Digital Object Identifier.
        ARK: Archival Resource Key.
        URL: Identifier is a standard URL.
        OTHER: Other unspecified identifier type.
    """
    HANDLE = "handle"
    DOI = "doi"
    ARK = "ark"
    URL = "url"
    OTHER = "other"

class DataAccess(str, Enum):
    """
    Enum representing the access mode for datasets.

    Args:
        OPEN (str): Data is openly accessible to the public.
        SHARED (str): Data is shared with specific groups or individuals under certain conditions.
        CLOSED (str): Data access is restricted and not publicly available.
    """
    OPEN = "open"
    SHARED = "shared"
    CLOSED = "closed"

class Certification(str, Enum):
    """
    Enum representing the certification types for dataset distribution hosts.

    Args:
        DIN31644: Certification according to DIN 31644 standard.
        DINI_ZERTIFIKAT: Certification by the German Initiative for Network Information (DINI).
        DSA: Data Seal of Approval certification.
        ISO16363: Certification based on the ISO 16363 standard for trustworthy digital repositories.
        ISO16919: Certification according to the ISO 16919 standard.
        TRAC: Certification based on the Trusted Repositories Audit & Certification (TRAC) standard.
        WDS: Certification from the World Data System (WDS).
        CORETRUSTSEAL: Certification by the CoreTrustSeal organization.
    """
    DIN31644 = "din31644"
    DINIZERTIFIKAT = "dini-zertifikat"
    DSA = "dsa"
    ISO16363 = "iso16363"
    ISO16919 = "iso16919"
    TRAC = "trac"
    WDS = "wds"
    CORETRUSTSEAL = "coretrustseal"

class PidSystem(str, Enum):
    """
    Enum representing the Persistent Identifier (PID) systems used for dataset distribution hosts.

    Args:
        ARK: Archival Resource Key (ARK) identifier system.
        ARXIV: arXiv identifier for preprints.
        BIBCODE: Bibliographic codes used in astronomy and astrophysics.
        DOI: Digital Object Identifier (DOI) system.
        EAN13: International Article Number (EAN-13) barcode standard.
        EISSN: Electronic International Standard Serial Number.
        HANDLE: Handle System for persistent digital identifiers.
        IGSN: International Geo Sample Number.
        ISBN: International Standard Book Number.
        ISSN: International Standard Serial Number.
        ISTC: International Standard Text Code.
        LISSN: Linking ISSN for serial publications.
        LSID: Life Science Identifier.
        PMID: PubMed Identifier for biomedical literature.
        PURL: Persistent Uniform Resource Locator.
        UPC: Universal Product Code.
        URL: Uniform Resource Locator.
        URN: Uniform Resource Name.
        OTHER: Other unspecified PID system.
    """
    ARK = "ark"
    ARXIV = "arxiv"
    BIBCODE = "bibcode"
    DOI = "doi"
    EAN13 = "ean13"
    EISSN = "eissn"
    HANDLE = "handle"
    IGSN = "igsn"
    ISBN = "isbn"
    ISSN = "issn"
    ISTC = "istc"
    LISSN = "lissn"
    LSID = "lsid"
    PMID = "pmid"
    PURL = "purl"
    UPC = "upc"
    URL = "url"
    URN = "urn"
    OTHER = "other"

class YesNoUnknown(str, Enum):
    """
    Enum representing a three-state option to indicate if a feature or option is supported.

    Args:
        YES: The option is supported.
        NO: The option is not supported.
        UNKNOWN: It is unknown if the option is supported.
    """
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"

class funding_id_type(str, Enum):
    """
    Suggested funder identifier types. Schema 1.2 takes any string here, so this enum is a
    convenience rather than a constraint.

    Args:
        FUNDREF: Identifier from the CrossRef Funder Registry.
        URL: A direct URL to the funder.
        OTHER: Other unspecified identifier type.
    """
    FUNDREF = "fundref"
    URL = "url"
    OTHER = "other"

class grant_id_type(str, Enum):
    """
    Suggested grant identifier types. Schema 1.2 takes any string here, so this enum is a
    convenience rather than a constraint.

    Args:
        URL: A direct URL to the grant.
        OTHER: Other unspecified identifier type.
    """
    URL = "url"
    OTHER = "other"

class FundingStatus(str, Enum):
    """
    Enum representing the possible funding statuses.

    Args:
        PLANNED: Funding has been planned but not yet applied for.
        APPLIED: Funding has been applied for but not yet granted.
        GRANTED: Funding has been awarded to the project.
        REJECTED: Funding application has been rejected.
    """
    PLANNED = "planned"
    APPLIED = "applied"
    GRANTED = "granted"
    REJECTED = "rejected"

class ContributorIdentifier(_MaDMPModel):
    """
    Represents a unique identifier for a contributor.

    Args:
        identifier (str): A unique identifier for the contributor, such as an ORCID. Example: "0000-0000-0000-0000".
        type (str): The type of identifier. Suggested values: orcid, isni, openid.
    """
    identifier: str
    type: str

class Contributor(_MaDMPModel):
    """
    Represents a contributor in a DMP.

    Args:
        affiliation (List[Affiliation]): The organisations the contributor belongs to.
        contributor_id (ContributorIdentifier): The identifier of the contributor, or a list of them.
        mbox (str): The email address of the contributor, validated as such (optional).
        name (str): The name of the contributor. Example: "John Smith".
        role (List[str]): The roles of the contributor, which may not repeat. Example: ["Data Steward"].
    """
    affiliation: Optional[list[Affiliation]] = None
    contributor_id: Annotated[
        Union[ContributorIdentifier, list[ContributorIdentifier]],
        AfterValidator(validate_id),
    ]
    mbox: Optional[Annotated[str, AfterValidator(validate_email)]] = None
    name: str
    role: Annotated[list[str], AfterValidator(validate_unique)]

class CreatorIdentifier(_MaDMPModel):
    """
    Represents a unique identifier for the creator of a dataset.

    Args:
        identifier (str): A unique identifier for the creator, such as an ORCID. Example: "0000-0003-0644-4174".
        type (str): The type of identifier. Suggested values: orcid, isni, openid.
    """
    identifier: str
    type: str

class Creator(_MaDMPModel):
    """
    Represents the creator of a dataset.

    Args:
        affiliation (List[Affiliation]): The organisations the creator belongs to.
        creator_id (CreatorIdentifier): The identifier of the creator, or a list of them.
        mbox (str): The creator's email address, validated as such. Example: "john.doe@example.com".
        name (str): The name of the creator. Example: "John Doe".
    """
    affiliation: Optional[list[Affiliation]] = None
    creator_id: Annotated[
        Union[CreatorIdentifier, list[CreatorIdentifier]],
        AfterValidator(validate_id),
    ]
    mbox: Optional[Annotated[str, AfterValidator(validate_email)]] = None
    name: str

class Cost(_MaDMPModel):
    """
    Represents a cost entry in a DMP.

    Args:
        currency_code (CurrencyCode): The currency code in ISO 4217 format. Example: "EUR".
        description (str): A brief description of the cost. Example: "Costs for maintaining...".
        title (str): The title of the cost entry. Example: "Storage and Backup".
        value (float): The numerical value of the cost. Example: 123.40.
    """
    currency_code: Optional[CurrencyCode] = None
    description: Optional[str] = None
    title: str
    value: Optional[float] = None

class HostIdentifier(_MaDMPModel):
    """
    Represents an identifier for the system hosting a dataset distribution.

    Args:
        identifier (str): A unique identifier for the host. Example: "http://example.org/repo".
        type (str): The type of identifier. Suggested value: url.
    """
    identifier: str
    type: str

class Host(_MaDMPModel):
    """
    Represents a dataset distribution host in a DMP. Information about the QoS provided by the infrastructure (e.g., repository) where data is stored.

    Args:
        availability (str): Availability percentage of the host. Example: "99.5".
        backup_frequency (str): Frequency at which backups are performed. Example: "weekly".
        backup_type (str): Type of backup storage used. Example: "tapes".
        certified_with (Certification): Certification type of the repository. Example: "coretrustseal".
        description (str): A description of the repository or host. Example: "Repository hosted by...".
        geo_location (CountryCode): Physical location of the repository, expressed using an ISO 3166-1 country code. Example: "AT".
        host_id (List[HostIdentifier]): Identifiers of the host.
        pid_system ([List[PidSystem]]): Persistent Identifier (PID) systems supported by the host. Example: ["doi"].
        storage_type (str): The type of storage used.  Example: "External Hard Drive".
        support_versioning (YesNoUnknown): Whether the host supports versioning.
        title (str): The title of the repository or host. Example: "Super Repository".
        url (AnyUrl): The URL of the system hosting a distribution of a dataset. Example: "https://zenodo.org".
    """
    availability: Optional[str] = None
    backup_frequency: Optional[str] = None
    backup_type: Optional[str] = None
    certified_with: Optional[Certification] = None
    description: Optional[str] = None
    geo_location: Optional[CountryCode] = None
    host_id: Optional[Annotated[list[HostIdentifier], AfterValidator(validate_id)]] = None
    pid_system: Optional[list[PidSystem]] = None
    storage_type: Optional[str] = None
    support_versioning: Optional[YesNoUnknown] = None
    title: str
    url: AnyUrl

class License(_MaDMPModel):
    """
    Represents a license applied to a dataset distribution.

    Args:
        license_ref (AnyUrl): URL link to the license document. Example: "https://creativecommons.org/licenses/by/4.0/".
        start_date (date): Date when the license starts being applicable. If set in the future, it indicates an embargo period.
    """
    license_ref: AnyUrl
    start_date: date

class Distribution(_MaDMPModel):
    """
    Represents a dataset distribution, providing technical information on a specific instance of data.

    Args:
        access_url (str): URL of the resource that gives access to a distribution of the dataset. Example: "http://some.repo".
        available_until (date): Date until the distribution is available.
        byte_size (int): Size of the dataset distribution in bytes.
        data_access (DataAccess): Access mode for the dataset (open, shared or closed). Required.
        description (str): Description of the dataset distribution. Example: "Best quality data before resizing".
        download_url (AnyUrl): URL to directly download the dataset.
        format (List[str]): Format of the dataset distribution. Example: ["image/tiff"].
        host (Host): Host information where the dataset is stored.
        issued (date): Date the distribution was published or released. Example: "2019-06-30".
        license (List[License]): Licenses applied to the dataset distribution.
        title (str): Title of the dataset distribution.
    """
    # access_url is the one URL-ish field the schema declares as a plain string, with no
    # format in any version. Modelling it as AnyUrl would reject documents the standard
    # accepts, so the recommendation stays in the description above.
    access_url: Optional[str] = None
    available_until: Optional[date] = None
    byte_size: Optional[int] = None
    data_access: DataAccess
    description: Optional[str] = None
    download_url: Optional[AnyUrl] = None
    format: Optional[list[str]] = None
    host: Optional[Host] = None
    issued: Optional[date] = None
    license: Optional[list[License]] = None
    title: str

class MetadataIdentifier(_MaDMPModel):
    """
    Represents an identifier for a metadata standard used in a dataset.

    Args:
        identifier (str): The identifier for the metadata standard. Example: "http://www.dublincore.org/specifications/dublin-core/dcmi-terms/".
        type (metadata_id_type): The type of identifier, restricted to "url" or "other".
    """
    identifier: str
    type: metadata_id_type

class Metadata(_MaDMPModel):
    """
    Represents metadata standards used in a dataset.

    Args:
        description (str): A description of the metadata standard. Example: "Provides taxonomy for...".
        language (LanguageEnum): The language in which the metadata is written, using ISO 639-3. Example: "eng".
        metadata_standard_id (MetadataIdentifier): The identifier of the metadata standard used, or a list of them.
    """
    description: Optional[str] = None
    language: LanguageEnum
    metadata_standard_id: Annotated[
        Union[MetadataIdentifier, Annotated[list[MetadataIdentifier], Field(min_length=1)]],
        AfterValidator(validate_id),
    ]

class SecurityPrivacy(_MaDMPModel):
    """
    Represents security and privacy measures applied to the dataset.

    Args:
        description (str): A description of security and privacy measures.
        title (str): The title of the security/privacy measure.
    """
    description: Optional[str] = None
    title: str

class TechnicalResourceIdentifier(_MaDMPModel):
    """
    Represents an identifier for a technical resource.

    Args:
        identifier (str): A unique identifier for the resource. Example: "https://example.org/resource".
        type (str): The type of identifier. Suggested value: url.
    """
    identifier: str
    type: str

class TechnicalResource(_MaDMPModel):
    """
    Represents technical resources needed to implement a DMP.

    Args:
        description (str): A description of the technical resource.
        name (str): The name of the technical resource.
        technical_resource_id (List[TechnicalResourceIdentifier]): Identifiers of the technical resource.
    """
    description: Optional[str] = None
    name: str
    technical_resource_id: Optional[Annotated[list[TechnicalResourceIdentifier],
                                              AfterValidator(validate_id)]] = None

class DatasetIdentifier(_MaDMPModel):
    """
    Represents an identifier for a dataset.

    Args:
        identifier (str): A unique identifier for the dataset. Example: "11353/10.923628".
        type (str): The type of identifier. Suggested values: handle, doi, ark, url.
    """
    identifier: str
    type: str


class Dataset(_MaDMPModel):
    """
    Represents a dataset within a DMP.

    Args:
        alternate_identifier (List[AlternateIdentifier]): Alternate identifiers of the dataset.
        creator (List[Creator]): The creators of the dataset.
        data_quality_assurance (List[str]): List of quality assurance measures.
        dataset_id (DatasetIdentifier): Identifier for the dataset.
        description (str): Description of the dataset.
        distribution (List[Distribution]): Technical distribution details.
        is_reused (bool): Whether the dataset is reused, that is, not produced in the projects this DMP covers.
        issued (date): Date of issue of the dataset.
        keyword (List[str]): Keywords describing the dataset.
        language (LanguageEnum): Language of the dataset.
        metadata (List[Metadata]): Metadata standards used.
        personal_data (YesNoUnknown): Indicates if the dataset contains personal data.
        preservation_statement (str): Description of dataset preservation measures.
        related_identifier (List[RelatedIdentifier]): Resources related to the dataset.
        rights (str): Rights not addressed by the license, such as copyright statements.
        security_and_privacy (List[SecurityPrivacy]): Security and privacy measures applied.
        sensitive_data (YesNoUnknown): Indicates if the dataset contains sensitive data.
        technical_resource (List[TechnicalResource]): Technical resources required.
        title (str): Title of the dataset.
        type (str): Type of dataset according to DataCite or COAR. Otherwise use the common name for the type, e.g. raw data, software, survey, etc.
    """
    alternate_identifier: Optional[Annotated[list[AlternateIdentifier],
                                             AfterValidator(validate_id)]] = None
    creator: Optional[list[Creator]] = None
    data_quality_assurance: Optional[list[str]] = None
    dataset_id: Annotated[DatasetIdentifier, AfterValidator(validate_id)]
    description: Optional[str] = None
    distribution: Optional[list[Distribution]] = None
    is_reused: Optional[bool] = None
    issued: Optional[date] = None
    keyword: Optional[list[str]] = None
    language: Optional[LanguageEnum] = None
    metadata: Optional[list[Metadata]] = None
    personal_data: YesNoUnknown
    preservation_statement: Optional[str] = None
    related_identifier: Optional[Annotated[list[RelatedIdentifier],
                                           AfterValidator(validate_id)]] = None
    rights: Optional[str] = None
    security_and_privacy: Optional[list[SecurityPrivacy]] = None
    sensitive_data: YesNoUnknown
    technical_resource: Optional[list[TechnicalResource]] = None
    title: str
    type: Optional[str] = None

class DMPIdentifier(_MaDMPModel):
    """
    Represents an identifier for the  DMP itself.

    Args:
        identifier (str): A unique identifier for the DMP. Example: "https://doi.org/10.1371/journal.pcbi.1006750".
        type (str): The type of identifier. Suggested values: handle, doi, ark, url.
    """
    identifier: str
    type: str

class FundingIdentifier(_MaDMPModel):
    """
    Represents the identifier of a funder.

    Args:
        identifier (str): The unique identifier for the funder. Example: "501100002428" (CrossRef Funder Registry ID).
        type (str): The type of identifier. Suggested values: fundref, url.
    """
    identifier: str
    type: str

class GrantIdentifier(_MaDMPModel):
    """
    Represents the identifier of a funding grant.

    Args:
        identifier (str): The unique identifier for the grant. Example: "776242" (Grant ID).
        type (str): The type of identifier. Suggested value: url.
    """
    identifier: str
    type: str

class Funding(_MaDMPModel):
    """
    Represents the funding details associated with a project.

    Args:
        funder_id (FundingIdentifier): The identifier of the funding organization.
        funding_status (FundingStatus): The status of the funding application. Example: "granted".
        grant_id (GrantIdentifier): The identifier of the grant associated with the project.
    """
    funder_id: Annotated[FundingIdentifier, AfterValidator(validate_id)]
    funding_status: Optional[FundingStatus] = None
    grant_id: Optional[Annotated[GrantIdentifier, AfterValidator(validate_id)]] = None

class ProjectIdentifier(_MaDMPModel):
    """
    Represents an identifier for a project.

    Args:
        identifier (str): A unique identifier for the project. Example: "https://example.org/project".
        type (str): The type of identifier. Suggested values: doi, raid, url.
    """
    identifier: str
    type: str

class Project(_MaDMPModel):
    """
    Represents a project related to a DMP.

    Args:
        title (str): The title of the project. Example: "Our New Project".
        description (str): A description of the project.
        end (date): The end date of the project.
        funding (List[Funding]): A list of funding sources related to the project.
        project_id (List[ProjectIdentifier]): Identifiers of the project.
        start (date): The start date of the project.
    """
    title: str
    description: Optional[str] = None
    end : Optional[date] = None
    funding : Optional[list[Funding]] = None
    project_id: Optional[Annotated[list[ProjectIdentifier], AfterValidator(validate_id)]] = None
    start : Optional[date] = None

class DMP(_MaDMPModel):
    """
    Represents a DMP.

    Args:
        alternate_identifier (List[AlternateIdentifier]): Alternate identifiers of the DMP.
        contact (Contact): The main contact person for the DMP.
        contributor (List[Contributor]): The people contributing to the DMP.
        cost (List[Cost]): The costs the DMP accounts for.
        created (datetime): The timestamp when the DMP was created.
        dataset (List[Dataset]): The datasets the DMP describes.
        description (str): A description of the DMP.
        dmp_id (DMPIdentifier): The unique identifier for the DMP.
        ethical_issues_description (str): A description of the ethical issues identified.
        ethical_issues_exist (YesNoUnknown): Whether ethical issues were identified.
        ethical_issues_report (str): Where the ethical issues report can be found. Preferably a URL, though the schema does not require one.
        language (LanguageEnum): The primary language of the DMP.
        modified (datetime): The timestamp when the DMP was last modified.
        project (List[Project]): The projects associated with this DMP.
        related_identifier (List[RelatedIdentifier]): Resources related to the DMP.
        title (str): The title of the DMP.
    """

    alternate_identifier: Optional[Annotated[list[AlternateIdentifier],
                                             AfterValidator(validate_id)]] = None
    title: str
    contact: Contact
    contributor: Optional[list[Contributor]] = None
    cost: Optional[list[Cost]] = None
    created: datetime
    dataset: list[Dataset]
    description: Optional[str] = None
    dmp_id: Annotated[DMPIdentifier, AfterValidator(validate_id)]
    ethical_issues_description: Optional[str] = None
    ethical_issues_exist: YesNoUnknown
    # Schema 1.2 dropped this field's format: uri, so a plain string is what it asks for.
    ethical_issues_report: Optional[str] = None
    language: LanguageEnum
    modified: datetime
    project: Optional[list[Project]] = None
    related_identifier: Optional[Annotated[list[RelatedIdentifier],
                                           AfterValidator(validate_id)]] = None
