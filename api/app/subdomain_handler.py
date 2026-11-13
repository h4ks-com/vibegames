import mimetypes
import os

from fastapi import HTTPException
from fastapi import Response
from fastapi import staticfiles
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

from app import github
from app.database import get_db
from app.project_naming import extract_subdomain
from app.project_naming import find_project_by_name_case_insensitive
from app.project_naming import get_host_from_headers
from app.project_naming import sanitize_project_name
from app.settings import settings

# Never served from a project's files: these belong to the platform itself.
RESERVED_PREFIXES = ("__api/", "__auth/")


class SubdomainStaticFiles(staticfiles.StaticFiles):
    """Custom StaticFiles that handles subdomain-based game serving."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_response(self, path: str, scope) -> StarletteResponse:
        """Override to check for subdomain games first."""

        if path.startswith(RESERVED_PREFIXES):
            raise HTTPException(status_code=404, detail="Not found")

        if settings.ENABLE_SUBDOMAINS:
            request = Request(scope)
            host = get_host_from_headers(dict(request.headers))

            if host:
                subdomain = extract_subdomain(host, settings.BASE_DOMAIN)
                if subdomain:
                    db: Session = next(get_db())
                    try:
                        game = find_project_by_name_case_insensitive(db, subdomain)

                        if game:
                            # Try serving the requested path first
                            requested_path = "index.html" if not path or path == "." else path
                            try:
                                content, media_type = github.get_file_content_with_type(game.project, requested_path)
                            except github.GithubFileNotFoundError:
                                # Only fall back to index.html for extensionless paths (SPA routing).
                                # Assets (.jpg, .css, .js, etc.) that don't exist should 404.
                                ext = os.path.splitext(requested_path)[1]
                                if ext and ext.lower() not in (".html", ".htm"):
                                    raise HTTPException(
                                        status_code=404,
                                        detail=f"File '{requested_path}' not found in project '{subdomain}'",
                                    )
                                try:
                                    content, media_type = github.get_file_content_with_type(game.project, "index.html")
                                except github.GithubFileNotFoundError:
                                    raise HTTPException(
                                        status_code=404,
                                        detail=f"File '{requested_path}' not found in project '{subdomain}'",
                                    )

                            # Update the number of opens for the game.
                            game.num_opens += 1
                            flag_modified(game, "num_opens")
                            db.commit()
                            return Response(content, media_type=media_type)

                        # If project not found, return detailed 404
                        sanitized_subdomain = sanitize_project_name(subdomain)
                        raise HTTPException(
                            status_code=404,
                            detail=f"Game project '{subdomain}' (sanitized: '{sanitized_subdomain}') not found",
                        )
                    finally:
                        db.close()

        # Fall back to regular static file serving
        return await super().get_response(path, scope)
