import re
import json
from pydantic import BaseModel, Field, AfterValidator, AnyUrl, ValidationError
from enum import Enum
from datetime import datetime
#from .dataset import Dataset
from typing import Optional
from typing_extensions import Annotated

## AUX IMPORTS

from languages import LanguageEnum
from currency_code import CurrencyCode
from country_code import CountryCode

## ENUMS

class contact_contributor_id_type(str, Enum):
    orcid = "orcid"
    isdi = "isdi"
    openid = "openid"
    other = "other"

## CONTACT

class ContactIdentifier(BaseModel):
    identifier: str
    type: contact_contributor_id_type

class Contact(BaseModel):
    """Contact person for a DMP"""
    name: str
    contact_id: ContactIdentifier
    mbox: str

class dmp_dataset_id_type(str, Enum):
    handle = "handle"
    doi = "doi"
    ark = "ark"
    url = "url"
    other = "other"

class DataAccess(str, Enum):
    open = "open"
    shared = "shared"
    closed = "closed"

class Certification(str, Enum):
    din31644 = "din31644"
    dinizertifikat = "dini-zertifikat"
    dsa = "dsa"
    iso16363 = "iso16363"
    iso16919 = "iso16919"
    trac = "trac"
    wds = "wds"
    coretrustseal = "coretrustseal"

class PidSystem(str, Enum):
    ark = "ark"
    arxiv = "arxiv"
    bibcode = "bibcode"
    doi ="doi"
    ean13= "ean13"
    eissn = "eissn"
    handle = "handle"
    igsn = "igsn"
    isbn = "isbn"
    issn = "issn"
    istc = "istc"
    lissn = "lissn"
    lsid = "lsid"
    pmid = "pmid"
    purl = "purl"
    upc = "upc"
    url = "url"
    urn = "urn"
    other = "other"

class YesNoUnknown(str, Enum):
    yes = "yes"
    no = "no"
    unknown = "unknown"

class funding_id_type(str, Enum):
    fundref = "fundref"
    url = "url"
    other = "other"

class grant_id_type(str, Enum):
    url = "url"
    other = "other"

class FundingStatus(str, Enum):
    planned = "planned"
    applied = "applied"
    granted = "granted"
    rejected = "rejected"

## CONTRIBUTOR

class ContributorIdentifier(BaseModel):
    identifier: str
    type: contact_contributor_id_type

class Contributor(BaseModel):
    contributor_id: ContributorIdentifier
    mbox: Optional[str] = None
    name: str
    role: list[str]

## COST

class Cost(BaseModel):
    currency_code: Optional[CurrencyCode] = None
    description: Optional[str] = None
    title: str
    value: Optional[float] = None

## DATASET

class Host(BaseModel):
    availability: Optional[str] = None
    backup_frequency: Optional[str] = None
    backup_type: Optional[str] = None
    certified_with: Optional[Certification] = None
    description: Optional[str] = None
    geo_location: Optional[CountryCode] = None
    pid_system: Optional[PidSystem] = None
    storage_type: Optional[str] = None
    support_versioning: Optional[YesNoUnknown] = None
    title: str
    url: AnyUrl
    
class License (BaseModel):
    license_ref: AnyUrl
    start_date: datetime

class Distribution(BaseModel):
    access_url: Optional[AnyUrl] = None
    available_until: Optional[datetime] = None
    byte_size: Optional[int] = None
    data_access: Optional[DataAccess] = None
    description: Optional[str] = None
    download_url: Optional[AnyUrl] = None
    format: Optional[list[str]] = None
    host: Optional[Host] = None
    license: Optional[list[License]] = None
    title: str

class MetadataIdentifier(BaseModel):
    identifier: str
    type: contact_contributor_id_type

class Metadata(BaseModel):
    description: Optional[str] = None
    language: LanguageEnum
    metadata_standard_id: MetadataIdentifier

class SecurityPrivacy(BaseModel):
    description: Optional[str] = None
    title: str

class TechnicalResource(BaseModel):
    description: Optional[str] = None
    name: str

class DatasetIdentifier(BaseModel):
    identifier: str
    type: dmp_dataset_id_type

class Dataset(BaseModel):
    data_quality_assurance: Optional[list[str]] = None
    dataset_id: DatasetIdentifier
    description: Optional[str] = None
    distribution: Optional[list[Distribution]] = None
    issued: Optional[datetime] = None
    keyword: Optional[list[str]] = None
    language: Optional[LanguageEnum] = None
    metadata: Optional[list[Metadata]] = None
    personal_data: YesNoUnknown
    preservation_statement: Optional[str] = None
    security_and_privacy: Optional[SecurityPrivacy] = None
    sensitive_data: YesNoUnknown
    technical_resource: Optional[list[TechnicalResource]] = None
    title: str
    type: Optional[str] = None

## DMP_ID

class DMPIdentifier(BaseModel):
    identifier: str
    type: dmp_dataset_id_type

## ethical_issues_report

class EthicalIssuesReport(BaseModel):
    uri: AnyUrl

## PROJECT

class FundingIdentifier(BaseModel):
    identifier: str
    type: funding_id_type

class GrantIdentifier(BaseModel):
    identifier: str
    type: grant_id_type

class Funding(BaseModel):
    funder_id: FundingIdentifier
    funding_status: Optional[FundingStatus] = None
    grant_id: Optional[GrantIdentifier] = None

class Project(BaseModel):
    title: str
    description: Optional[str] = None
    start : Optional[datetime] = None # should be ISO8601 when serialized
    end : Optional[datetime] = None # should be ISO8601 when serialized
    funding : Optional[Funding] = None

# AUX FUNCTIONS

def validate_dmp_id(value: DMPIdentifier):
    pass
    # match value.type:
    #     case "doi":
    #         doi_pattern = r"^10.\d{4,9}/[-._;()/:A-Z0-9]+$"
    #         assert re.match(doi_pattern, value.identifier, re.IGNORECASE), "Invalid DOI format"
    #     case "orcid":
    #         orcid_pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]{1}$"
    #         assert re.match(orcid_pattern, value.identifier), "Invalid ORCID format"
    #     case "ark":
    #         ark_pattern = r"(/?ark:/? ?)([-a-zA-Z0-9@:%_\\+.~#?&//=]*)"
    #         assert re.match(ark_pattern, value.identifier), "Invalid ARK format"
    #     case "handle": # provisional de ChatGPT
    #         handle_pattern = r"^\\d+\\.\\d+/[a-zA-Z0-9._;()/:@&=+$,-]+$"
    #         assert re.match(handle_pattern, value.identifier), "Invalid Handle format"
    #     case "other":
    #         assert value.identifier != ""


### DMP

class DMP(BaseModel):
    title: str
    contact: Contact 
    #= Field(default=Contact(name="change-me", 
    #                                  contact_id=ContactIdentifier("changeme", "other"), 
    #                                  mbox="change-me"))
    
    contributor: list[Contributor] = Field(
                                        default=[
                                            Contributor(
                                                contributor_id=ContributorIdentifier(identifier="other", type="other"), 
                                                name="Contributor", 
                                                role=["role"]
                                            )
                                        ]
                                    )

    cost: Optional[list[Cost]] = None
    
    created: datetime = Field(default=datetime.now().replace(microsecond=0).isoformat()) # should be ISO8601 when serialized

    dataset: list[Dataset] = Field(
                                default=[
                                    Dataset(
                                        dataset_id=DatasetIdentifier(identifier="doi", type="doi"),
                                        description="change-me",
                                        personal_data="no",
                                        sensitive_data="no",
                                        technical_resource=[TechnicalResource(name="resource")],
                                        title="Dataset"
                                        )
                                ]
                            )
    
    description: Optional[str] = None

    dmp_id: Annotated[DMPIdentifier, AfterValidator(validate_dmp_id)] \
        = Field(default = DMPIdentifier(identifier="change-me", type="other"))

    ethical_issues_description: Optional[str] = None
    ethical_issues_exist: Optional[YesNoUnknown] = None
    ethical_issues_report: Optional[str] = None # URI format
    
    language: LanguageEnum
    
    modified: datetime = Field(default=datetime.now().replace(microsecond=0).isoformat()) # should be ISO8601 when serialized
    

# TEST DMP

with open('../../../json_dmps/ex10-fairsharing.json', 'r') as file:
    data = json.load(file)

testDMP = DMP(**data['dmp'])  

try:
    testDMP = DMP(**data['dmp'])
    print("DMP valid!")
except ValidationError as e:
    print("ERROR!")
    print(e.errors())
