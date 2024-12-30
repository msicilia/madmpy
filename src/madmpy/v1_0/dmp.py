from pydantic import BaseModel
class Project(BaseModel):
    title: str
    description: str | None
    start : datetime # should be ISO8601 when serialized
    end : datetime # should be ISO8601 when serialized
    funding : Funding | None