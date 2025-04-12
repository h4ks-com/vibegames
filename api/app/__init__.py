from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routes import router

WORKERS = 4  # Number of worker threads for handling requests


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # Create the database and tables if they do not exist.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Project manager API",
    description="Manage and browse github game projects",
    lifespan=lifespan,
)

app.include_router(router)
