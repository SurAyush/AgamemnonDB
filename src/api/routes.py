
from fastapi import APIRouter

from api.schemas import (
    InsertRequest,
    InsertResponse,
    SearchRequest,
    SearchResponse,
    DeleteRequest,
    DeleteResponse,
)

router = APIRouter()


@router.post("/vectors", response_model=InsertResponse)
async def insert_vector(request: InsertRequest):
    # TODO: Connect to database write engine
    return InsertResponse(id=1)


@router.delete("/vectors/{vector_id}", response_model=DeleteResponse)
async def delete_vector(request: DeleteRequest):
    # TODO: Connect to database delete engine
    return DeleteResponse(
        id=request.id,
        deleted=True
    )


@router.post("/search", response_model=SearchResponse)
async def search_vectors(request: SearchRequest):
    # TODO: Connect to database query engine
    return SearchResponse(results=[])
