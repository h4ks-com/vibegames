from fastapi import HTTPException
from fastapi import Response
from fastapi.staticfiles import StaticFiles
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


class SubdomainStaticFiles(StaticFiles):
    """Custom StaticFiles that handles subdomain-based game serving."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_response(self, path: str, scope) -> StarletteResponse:
        """Override to check for subdomain games first."""

        if settings.ENABLE_SUBDOMAINS:
            request = Request(scope)
            host = get_host_from_headers(dict(request.headers))

            if host:
                subdomain = extract_subdomain(host, settings.BASE_DOMAIN)
                if subdomain:
                    # Try to serve the game directly
                    db: Session = next(get_db())
                    try:
                        # Find project with case-insensitive sanitized lookup
                        game = find_project_by_name_case_insensitive(db, subdomain)

                        if game:
                            try:
                                content = github.get_file_content(game.project)
                                # Update the number of opens for the game.
                                game.num_opens += 1
                                flag_modified(game, "num_opens")
                                db.commit()
                                return Response(content, media_type="text/html")
                            except github.GithubFileNotFoundError:
                                pass

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
