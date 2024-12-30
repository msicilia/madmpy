from pydantic import BaseModel, Field, AfterValidator
from enum import Enum
from datetime import datetime
from .dataset import Dataset
from typing import Optional
from typing_extensions import Annotated


class dmp_id_type(str, Enum):
    handle = "handle"
    doi = "doi"
    ark = "ark"
    url = "url"
    other = "other"


class DMPIdentifier(BaseModel):
    identifier: str
    type: dmp_id_type


def validate_dmp_id(value: DMPIdentifier):
    match value.type:
        case "doi":
            assert value.identifier.startswith("https://doi.org/")
        case "other":
            assert value.identifier != ""


class Funding(BaseModel):
    funder_id: str
    funding_status: str | None
    grant_id: str | None

class Project(BaseModel):
    title: str
    description: str | None
    start : datetime | None # should be ISO8601 when serialized
    end : datetime | None # should be ISO8601 when serialized
    funding : Funding | None

class contact_id_type(str, Enum):
    orcid = "orcid"
    isdi = "isdi"
    openid = "openid"
    other = "other"

class ContactIdentifier(BaseModel):
    identifier: str
    type: contact_id_type


class Contact(BaseModel):
    """Contact person for a DMP"""
    name: str
    contact_id: ContactIdentifier
    mbox: str

class DMP(BaseModel):
    title: str
    dmp_id: Annotated[DMPIdentifier, AfterValidator(validate_dmp_id)] \
        = Field(default = DMPIdentifier(identifier="change-me", type="other"))
    description: Optional[str] = None
    created: datetime = Field(default=datetime.now()) # should be ISO8601 when serialized
    contact : Contact 
    #= Field(default=Contact(name="change-me", 
     #                                         contact_id=ContactIdentifier("changeme", "other"), 
     #                                         mbox="change-me"))
    dataset: list[Dataset] = Field(default=[Dataset(description="change-me")])


