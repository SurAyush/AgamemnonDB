from pydantic import BaseModel, Field


class InsertRequest(BaseModel):
    vector: list[float]
    metadata: dict = Field(default_factory=dict)


class InsertResponse(BaseModel):
    id: int


class SearchRequest(BaseModel):
    vector: list[float]
    k: int = Field(default=5, gt=0, lt=100, description="Number of nearest neighbors to return (1-100)")


class SearchResult(BaseModel):
    id: int
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: list[SearchResult]


class DeleteRequest(BaseModel):
    id: int

class DeleteResponse(BaseModel):
    id: int
    deleted: bool
