from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router

import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting AgamemnonDB...")

    # TODO: Initialize database engine
    # app.state.db = VectorDB(...)

    yield

    # TODO: Close database engine
    print("Shutting down AgamemnonDB...")


app = FastAPI(
    title="AgamemnonDB",
    description="LSM-inspired dynamic HNSW vector database",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
