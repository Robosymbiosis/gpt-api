from typing import Any
from typing import List
from typing import Optional

from fastapi import Query
from pydantic import BaseModel
from pydantic import Field


class SearchRequest(BaseModel):
    database: str = Query(
        ...,
        description="The name of the database to search in (godot, odoo, fusion)",
    )
    query: str = Query(..., description="The query to search for")


# Model for a single search result item
class SearchResultItem(BaseModel):
    url_link: str = Field(..., description="The URL where you can find the information")
    similarity: float = Field(
        ..., description="How close the context is to the initial search query"
    )
    context: str = Field(..., description="The context of the search result item")


# Model for the search endpoint's response
class SearchResponse(BaseModel):
    results: Optional[List[SearchResultItem]] = Field(
        default=[], description="List of search result items"
    )
