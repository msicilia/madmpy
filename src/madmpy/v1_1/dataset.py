from pydantic import BaseModel, Field
from datetime import datetime
import json

class Dataset(BaseModel):
    title: str = Field(default="CHANGE_ME")
    description: str | None = ""
    language: str | None = None
    def to_dcat(self):
        """Returns a DCAT representation of the dataset"""
        lang = self.language if self.language else "und"
        fragment ={"@id":"http://changeme/dataset1",
                     "@type":["http://www.w3.org/ns/dcat#Dataset"],
                     "http://purl.org/dc/terms/title":[{"@value":self.title,"@language":lang}],
                     "http://purl.org/dc/terms/identifier":[{"@value":"http://changeme/dataset1"}],
                     "http://purl.org/dc/terms/description":[{"@value":self.description,"@language":lang}],
                    }
        return json.dumps(fragment)