import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.db_migrations import run_migrations
from app.models import Base
from app.routes import router
from app.settings import settings
from app.subdomain_handler import SubdomainStaticFiles

WORKERS = 4  # Number of worker threads for handling requests


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # Create the database and tables if they do not exist.
    try:
        Base.metadata.create_all(bind=engine)
        run_migrations()
    except Exception as e:
        logging.error(f"Error creating database table at {settings.DB_PATH}: {e}")
        raise e
    yield


app = FastAPI(
    title="Project manager API",
    description="Manage and browse github game projects",
    lifespan=lifespan,
    redirect_slashes=True,
)

app.include_router(router)
app.mount("/", SubdomainStaticFiles(directory="static", html=True), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
