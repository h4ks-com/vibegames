import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import auth_routes
from app import rows
from app.database import engine
from app.db_migrations import run_migrations
from app.errors import ApiError
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

if settings.OBBY_ENABLED:
    # User identity and the per-app rows API. Mounted before the catch-all static handler,
    # so /__api and /__auth can never be served from a project's files.
    app.include_router(auth_routes.router)
    app.include_router(rows.router)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


app.mount("/", SubdomainStaticFiles(directory="static", html=True), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
