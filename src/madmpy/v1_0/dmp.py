from pydantic import BaseModel, Field, AfterValidator, AnyUrl
from enum import Enum
from datetime import datetime
from typing import Optional
from typing_extensions import Annotated
import re

from ..languages import LanguageEnum
from ..currency_code import CurrencyCode
from ..country_code import CountryCode

def extract_identifier(url, id_type):
    """
    Extracts the identifier from a URL based on the specified type.

    Args:
        url (str): The URL containing the identifier.
        id_type (str): The type of identifier to extract. Supported types are "doi", "orcid", "ark", and "handle".

    Returns:
        str or None: The extracted identifier if found, otherwise None.
    """
    patterns = {
        "doi": r"10\.\d{4,9}/[-._;()/:A-Z0-9]+$",
        "orcid": r"\d{4}-\d{4}-\d{4}-\d{3}[0-9X]{1}$",
        "ark": r"ark:/[-a-zA-Z0-9@:%_\\+.~#?&//=]+$",
        "handle": r"\d+\.\d+/[a-zA-Z0-9._;()/:@&=+$,-]+$"
    }
    
    if id_type not in patterns:
        return url
    
    match = re.search(patterns[id_type], url, re.IGNORECASE)
    return match.group(0) if match else None

def validate_id(value):
    """
    Validates an identifier.

    Args:
        value (object): An object containing `type` and `identifier` attributes.

    Raises:
        ValueError: If the object does not have `type` and `identifier` attributes.
        ValueError: If the identifier does not match the expected format for its type.

    Returns:
        object: The validated `value` object.
    """
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
            ark_pattern = r"^ark:\/\d{5,10}\/[\w\-.]+(\?[^\s#]+|#[^\s]+)?$"
            if not re.match(ark_pattern, identifier):
                raise ValueError("Invalid ARK format")
        case "handle":
            handle_pattern = r"\d{1,5}(\.\d+)?\/[\w\-.]+$"
            if not re.match(handle_pattern, identifier):
                raise ValueError("Invalid Handle format")
        case "other":
            if not identifier:
                raise ValueError("Identifier cannot be empty for 'other'")
        case _:
            raise ValueError("Unsupported identifier type")
    
    return value

class metadata_id_type(str, Enum):
    """
    Enum for allowed metadata identifier types.
    
    Args:
        URL: Identifier type is a URL.
        OTHER: Other unspecified identifier type.
    """
    URL = "url"
    OTHER = "other"

class contact_id_type(str, Enum):
    """
    Enum for allowed contact identifier types.
    
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
    Enum for allowed contributor identifier types.
    
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

class ContactIdentifier(BaseModel):
    """
    Represents a unique identifier for the contact person in a DMP.

    Args:
        identifier (str): A unique identifier for the contact, such as an ORCID URL. Example: "https://orcid.org/0000-0003-0644-4174".
        type (contact_id_type): The type of identifier, restricted to specific values (orcid, isni, openid, other) as defined in the schema.
    """
    identifier: str
    type: contact_id_type

class Contact(BaseModel):
    """
    Represents the main contact person for a DMP.
    
    Args:
        name (str): The name of the contact person. Example: "Charlie Chaplin".
        contact_id (ContactIdentifier): The unique identifier for the contact, including an identifier value and type.
        mbox (str): The contact person's email address. Example: "cc@example.com".
    """
    name: str
    contact_id: ContactIdentifier
    mbox: str

class dmp_dataset_id_type(str, Enum):
    """
    Enum for allowed DMP dataset identifier types.
    
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
    Enum representing the allowed identifier types for funders.
    
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
    Enum representing the allowed identifier types for grants.
    
    Args:
    - URL: A direct URL to the grant.
    - OTHER: Other unspecified identifier type.
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

class ContributorIdentifier(BaseModel):
    """
    Represents a unique identifier for a contributor.

    Args:
        identifier (str): A unique identifier for the contact, such as an ORCID URL. Example: "https://orcid.org/0000-0000-0000-0000".
        type (contributor_id_type): The type of identifier, restricted to specific values (orcid, isni, openid, other) as defined in the schema.
    """
    identifier: str
    type: contributor_id_type

class Contributor(BaseModel):
    """
    Represents a contributor in a DMP.

    Args:
        contributor_id (ContributorIdentifier): The unique identifier for the contributor.
        mbox (str): The email address of the contributor (optional).
        name (str): The name of the contributor. Example: "John Smith".
        role (List[str]): The roles of the contributor, at least one role is required. Example: ["Data Steward"].
    """
    contributor_id: ContributorIdentifier
    mbox: Optional[str] = None
    name: str
    role: list[str] = Field(min_length=1)

class Cost(BaseModel):
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

class Host(BaseModel):
    """
    Represents a dataset distribution host in a DMP. Information about the QoS provided by the infrastructure (e.g., repository) where data is stored.
    
    Args:
        availability (str): Availability percentage of the host. Example: "99.5".
        backup_frequency (str): Frequency at which backups are performed. Example: "weekly".
        backup_type (str): Type of backup storage used. Example: "tapes".
        certified_with (Certification): Certification type of the repository. Example: "coretrustseal".
        description (str): A description of the repository or host. Example: "Repository hosted by...".
        geo_location (CountryCode): Physical location of the repository, expressed using an ISO 3166-1 country code. Example: "AT".
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
    pid_system: Optional[list[PidSystem]] = None
    storage_type: Optional[str] = None
    support_versioning: Optional[YesNoUnknown] = None
    title: str
    url: AnyUrl
    
class License (BaseModel):
    """
    Represents a license applied to a dataset distribution.
    
    Args:
        license_ref (AnyUrl): URL link to the license document. Example: "https://creativecommons.org/licenses/by/4.0/".
        start_date (datetime): Date when the license starts being applicable. If set in the future, it indicates an embargo period.
    """
    license_ref: AnyUrl
    start_date: datetime

class Distribution(BaseModel):
    """
    Represents a dataset distribution, providing technical information on a specific instance of data.
    
    Args:
        access_url (AnyUrl): URL of the resource that gives access to a distribution of the dataset. Example: "http://some.repo".
        available_until (datetime): Date until the distribution is available.
        byte_size (int): Size of the dataset distribution in bytes.
        data_access (DataAccess): Access mode for the dataset (open, shared or closed).
        description (str): Description of the dataset distribution. Example: "Best quality data before resizing".
        download_url (AnyUrl): URL to directly download the dataset.
        format (List[str]): Format of the dataset distribution. Example: ["image/tiff"].
        host (Host): Host information where the dataset is stored.
        license (List[License]): Licenses applied to the dataset distribution, at least one license is required.
        title (str): Title of the dataset distribution.
    """
    access_url: Optional[AnyUrl] = None
    available_until: Optional[datetime] = None
    byte_size: Optional[int] = None
    data_access: Optional[DataAccess] = None
    description: Optional[str] = None
    download_url: Optional[AnyUrl] = None
    format: Optional[list[str]] = None
    host: Optional[Host] = None
    license: Optional[list[License]] = Field(None, min_length=1)
    title: str

class MetadataIdentifier(BaseModel):
    """
    Represents an identifier for a metadata standard used in a dataset.
    
    Args:
        identifier (str): The identifier for the metadata standard. Example: "http://www.dublincore.org/specifications/dublin-core/dcmi-terms/".
        type (str): The type of identifier, restricted to "url" or "other".
    """
    identifier: str
    type: metadata_id_type

class Metadata(BaseModel):
    """
    Represents metadata standards used in a dataset.
    
    Args:
        description (str): A description of the metadata standard. Example: "Provides taxonomy for...".
        language (LanguageEnum): The language in which the metadata is written, using ISO 639-3. Example: "eng".
        metadata_standard_id (MetadataIdentifier): The identifier of the metadata standard used.
    """
    description: Optional[str] = None
    language: LanguageEnum
    metadata_standard_id: MetadataIdentifier

class SecurityPrivacy(BaseModel):
    """
    Represents security and privacy measures applied to the dataset.
    
    Args:
        description (str): A description of security and privacy measures.
        title (str): The title of the security/privacy measure.
    """
    description: Optional[str] = None
    title: str

class TechnicalResource(BaseModel):
    """
    Represents technical resources needed to implement a DMP.
    
    Args:
        description (str): A description of the technical resource.
        name (str): The name of the technical resource.
    """
    description: Optional[str] = None
    name: str

class DatasetIdentifier(BaseModel):
    """
    Represents an identifier for a dataset.
    
    Args:
        identifier (str): A unique identifier for the dataset. Example: "https://hdl.handle.net/11353/10.923628".
        type (dmp_dataset_id_type): The type of identifier, must be one of the allowed values (handle, doi, ark, url, other).
    """
    identifier: str
    type: dmp_dataset_id_type

class Dataset(BaseModel):
    """
    Represents a dataset within a DMP.
    
    Args:
        data_quality_assurance (List[str]): List of quality assurance measures.
        dataset_id (DatasetIdentifier): Identifier for the dataset.
        description (str): Description of the dataset.
        distribution (List[Distribution]): Technical distribution details.
        issued (datetime): Date of issue of the dataset.
        keyword (List[str]): Keywords describing the dataset.
        language (LanguageEnum): Language of the dataset.
        metadata (List[Metadata]): Metadata standards used, at least one metadata is required.
        personal_data (YesNoUnknown): Indicates if the dataset contains personal data.
        preservation_statement (str): Description of dataset preservation measures.
        security_and_privacy (List[SecurityPrivacy]): Security and privacy measures applied, at least one measure is required.
        sensitive_data (YesNoUnknown): Indicates if the dataset contains sensitive data.
        technical_resource (List[TechnicalResource]): Technical resources required.
        title (str): Title of the dataset.
        type (str): Type of dataset according to DataCite or COAR. Otherwise use the common name for the type, e.g. raw data, software, survey, etc.
    """
    data_quality_assurance: Optional[list[str]] = None
    #dataset_id: DatasetIdentifier
    dataset_id: Annotated[DatasetIdentifier, AfterValidator(validate_id)] # \
    description: Optional[str] = None
    distribution: Optional[list[Distribution]] = None
    issued: Optional[datetime] = None
    keyword: Optional[list[str]] = None
    language: Optional[LanguageEnum] = None
    metadata: Optional[list[Metadata]] = Field(None, min_length=1)
    personal_data: YesNoUnknown
    preservation_statement: Optional[str] = None
    security_and_privacy: Optional[list[SecurityPrivacy]] = Field(None, min_length=1)
    sensitive_data: YesNoUnknown
    technical_resource: Optional[list[TechnicalResource]] = None
    title: str
    type: Optional[str] = None

class DMPIdentifier(BaseModel):
    """
    Represents an identifier for the  DMP itself.
    
    Args:
        identifier (str): A unique identifier for the DMP. Example: "https://doi.org/10.1371/journal.pcbi.1006750".
        type (dmp_dataset_id_type): The type of identifier, must be one of the allowed values. Example: "doi".
    """
    identifier: str
    type: dmp_dataset_id_type

class FundingIdentifier(BaseModel):
    """
    Represents the identifier of a funder.

    Args:
        identifier (str): The unique identifier for the funder. Example: "501100002428" (CrossRef Funder Registry ID).
        type (FundingIdType): The type of funder identifier, must be one of the allowed values: fundref, url, other.
    """
    identifier: str
    type: funding_id_type

class GrantIdentifier(BaseModel):
    """
    Represents the identifier of a funding grant.

    Args:
        identifier (str): The unique identifier for the grant. Example: "776242" (Grant ID).
        type (GrantIdType): The type of grant identifier, must be one of the allowed values: url, other.
    """
    identifier: str
    type: grant_id_type

class Funding(BaseModel):
    """
    Represents the funding details associated with a project.
    
    Args:
        funder_id (FundingIdentifier): The identifier of the funding organization.
        funding_status (FundingStatus): The status of the funding application. Example: "granted".
        grant_id (GrantIdentifier): The identifier of the grant associated with the project.
    """
    funder_id: FundingIdentifier
    funding_status: Optional[FundingStatus] = None
    grant_id: GrantIdentifier

class Project(BaseModel):
    """
    Represents a project related to a DMP.
    
    Args:
        title (str): The title of the project. Example: "Our New Project".
        description (str): A description of the project.
        start (datetime): The start date of the project.
        end (datetime): The end date of the project.
        funding (List[Funding]): A list of funding sources related to the project.
    """
    title: str
    description: Optional[str] = None
    start : datetime
    end : datetime
    funding : Optional[list[Funding]] = None

class DMP(BaseModel):
    """
    Represents a DMP.

    Args:
        title (str): The title of the DMP.
        project (Project): The project associated with this DMP.
        created (datetime): The timestamp when the DMP was created.
        modified (datetime): The timestamp when the DMP was last modified.
        language (LanguageEnum): The primary language of the DMP.
        description (Optional[str]): A description of the DMP.
        dmp_id (DMPIdentifier): The unique identifier for the DMP.
    """
        
    title: str
    contact: Contact 
    contributor: list[Contributor] = None
    cost: Optional[list[Cost]] = None
    created: datetime
    dataset: list[Dataset]
    description: Optional[str] = None
    dmp_id: Annotated[DMPIdentifier, AfterValidator(validate_id)] # \
    #     = Field(default = DMPIdentifier(identifier="change-me", type="other"))
    ethical_issues_description: Optional[str] = None
    ethical_issues_exist: Optional[YesNoUnknown] = None
    ethical_issues_report: Optional[AnyUrl] = None
    language: LanguageEnum
    modified: datetime
    project: Optional[list[Project]] = None

    # contact: Contact = Field(default=Contact(name="change-me", 
    #                                  contact_id=ContactIdentifier("changeme", "other"), 
    #                                  mbox="change-me"))
    # contributor: list[Contributor] = Field(
    #                                     default=[
    #                                         Contributor(
    #                                             contributor_id=ContributorIdentifier(identifier="other", type="other"), 
    #                                             name="Contributor", 
    #                                             role=["role"]
    #                                         )
    #                                     ]
    #                                 )
    # dataset: list[Dataset] = Field(
    #                             default=[
    #                                 Dataset(
    #                                     dataset_id=DatasetIdentifier(identifier="doi", type="doi"),
    #                                     description="change-me",
    #                                     personal_data="no",
    #                                     sensitive_data="no",
    #                                     technical_resource=[TechnicalResource(name="resource")],
    #                                     title="Dataset"
    #                                     )
    #                             ], min_length=1
    #                         )
    # project: list[Project] = Field(default=[
    #                             Project(
    #                                 title="Project Title",
    #                                 description="Project's description",
    #                                 start=datetime.now().replace(microsecond=0).isoformat(),
    #                                 end=datetime.now().replace(microsecond=0).isoformat(),
    #                                 funding=[
    #                                             Funding(
    #                                                 funder_id=FundingIdentifier(identifier="501100002428", type="fundref"),
    #                                                 funding_status=FundingStatus.GRANTED,
    #                                                 grant_id=GrantIdentifier(identifier="776242", type="other")
    #                                             )
    #                                         ]
    #                                 )   
    #                             ]
    #                         )