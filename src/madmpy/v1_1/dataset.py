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
        fragment ={ "@id":"http://changeme/dataset1", # Preguntar a MA
                    "@type":["http://www.w3.org/ns/dcat#Dataset"], # Preguntar a MA
                    "http://purl.org/dc/terms/title":[{"@value":self.title,"@language":lang}],
                    "http://purl.org/dc/terms/identifier":[{"@value":"http://changeme/dataset1"}],
                    "http://purl.org/dc/terms/description":[{"@value":self.description,"@language":lang}],
                    "http://purl.org/dc/elements/1.1/subject":[{"@value":self.keyword,"@language":lang}],
                    "http://purl.org/dc/terms/language":[{"@value":self.language,"@language":lang}],
                    "http://purl.org/dc/terms/issued":[{"@value":self.issued,"@language":lang}],
                    "http://purl.org/dc/terms/type":[{"@value":self.type,"@language":lang}],
                    }
        return json.dumps(fragment)
   

# https://www.dublincore.org/specifications/dublin-core/dcmi-terms/