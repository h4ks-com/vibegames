import json
import logging
import mimetypes
from datetime import datetime
from typing import Literal

import pytz
from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app import g4f
from app import github
from app import thumbs
from app.auth import get_api_key
from app.database import get_db
from app.models import Game
from app.settings import settings

router = APIRouter()
admin_router = APIRouter(tags=["Admin"], prefix="/admin")
file_router = APIRouter(tags=["File management"], prefix="/api")
ai_router = APIRouter(tags=["AI"], prefix="/api/ai")
games_router = APIRouter(tags=["Games"], prefix="/game")


class RequestBody(BaseModel):
    content: str


@admin_router.get("/reset")
def reset_db(
    _: str = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> list[str]:
    """
    Initialize the database and create the necessary entries from github
    """
    names = github.get_projects()
    # Truncate the database.
    db.query(Game).delete()
    db.commit()
    # Recreate the database entries.
    for name in names:
        game = Game(project=name, date_added=datetime.now(pytz.utc), date_modified=datetime.now(pytz.utc), num_opens=0)
        db.add(game)
    db.commit()
    return names


@admin_router.get("/create_thumbnails")
def create_thumbnails(
    request: Request,
    _: str = Depends(get_api_key),
    db: Session = Depends(get_db),
    force_recreate: bool = Query(False, description="Force recreate thumbnails"),
) -> JSONResponse:
    """Create game thumbnails sequentially. Can be very slow."""
    # Load all games from the database.
    success = []
    failed = []
    games = db.query(Game).all()
    for game in games:
        html_path = str(request.url_for("get_game_html", project=game.project).path)
        game_url = f"{settings.APP_URL}{html_path}"
        logging.info(f"Creating thumbnail for {game_url}")
        try:
            thumbs.refresh_thumb(game_url, force_recreate=force_recreate)
            success.append(game.project)
        except Exception as e:
            logging.error(f"Failed to create thumbnail for {game_url}: {e}")
            failed.append(game.project)
    return JSONResponse(
        {
            "status": "success",
            "success": success,
            "failed": failed,
        }
    )


@file_router.put("/project/{project_name}/{file_path:path}")
def upload_file(
    request: Request,
    body: RequestBody = Body(..., description="File content"),
    project_name: str = Path(..., description="Project name"),
    file_path: str = Path(..., description="File path"),
    auth: str = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Update or create a file inside a project folder in GitHub.
    - If the project does not exist in the database, create a new row.
    - If it exists, update the modification timestamp.
    """
    content = body.content
    try:
        github.update_or_create_file(file_path, content, project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Update database entry.
    game: Game | None = db.query(Game).filter(Game.project == project_name).first()
    now = datetime.now(pytz.utc)
    if game is None:
        game = Game(project=project_name, date_added=now, date_modified=now, num_opens=0)
        db.add(game)
    else:
        game.date_modified = now
        flag_modified(game, "date_modified")
    db.commit()
    html_path = str(request.url_for("get_game_html", project=game.project).path)

    # TODO might not need to create a thumb for every file
    thumb_url = thumbs.get_thumb_url(f"{settings.APP_URL}{html_path}")
    background_tasks = BackgroundTasks()
    background_tasks.add_task(thumbs.refresh_thumb, f"{settings.APP_URL}{html_path}")
    response = JSONResponse(
        {
            "status": "success",
            "html_path": html_path,
            "thumb_url": thumb_url,
        }
    )
    response.background = background_tasks
    return response


def update_context_json(project_name: str, project: g4f.Project) -> None:
    try:
        github.update_or_create_file(
            "context.json",
            project.context.model_dump_json(indent=2),
            project_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_router.post("/{project_name}")
def create_ai_project(
    request: Request,
    body: RequestBody = Body(..., description="Prompt for AI to generate the project"),
    project_name: str = Path(..., description="Project name"),
    auth: str = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Create a new project in GitHub using G4F API.
    - The project will be created under the specified path.
    - The content will be the AI generated HTML.
    """
    prompt = body.content
    # Raise an error if the project already exists.
    game: Game | None = db.query(Game).filter(Game.project == project_name).first()
    if game is not None:
        raise HTTPException(status_code=400, detail="Project already exists")

    try:
        project = g4f.create_project(prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    update_context_json(project_name, project)
    return upload_file(
        request=request,
        project_name=project_name,
        file_path="index.html",
        body=RequestBody(content=project.files[0].content),
        db=db,
        auth=auth,
    )


@ai_router.put("/{project_name}")
def update_ai_project(
    request: Request,
    body: RequestBody = Body(..., description="Prompt for AI to generate HTML"),
    project_name: str = Path(..., description="Project name"),
    auth: str = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Update an existing project in GitHub using G4F API.
    - The project will be updated under the specified path.
    - The content will be the AI generated HTML.
    """
    prompt = body.content
    # Raise an error if the project does not exist.
    game: Game | None = db.query(Game).filter(Game.project == project_name).first()
    if game is None:
        raise HTTPException(status_code=400, detail="Project does not exist")

    try:
        context_str = github.get_file_content(project_name, "context.json")
        messages = g4f.Context.model_validate_json(context_str).messages
    except github.GithubFileNotFoundError:
        messages = []
        try:
            content = github.get_file_content(project_name, "index.html")
            messages.append(
                g4f.Message(
                    role="user",
                    content=f"Please use the following code as a base to update:\n```\n{content}\n```",
                )
            )
        except github.GithubFileNotFoundError:
            pass
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid context file") from e
    except ValidationError as e:
        raise HTTPException(status_code=400, detail="Invalid context file format") from e

    # We need to make the bot aware if the user is the last committer of the file.
    if not github.is_last_committer_token_user(project_name, "index.html"):
        content = github.get_file_content(project_name, "index.html")
        messages.append(
            g4f.Message(
                role="user",
                content=f"I have modified the codebase to:\n```\n{content}\n```. Please use this as a base to update the code.",
            )
        )

    try:
        project = g4f.edit_project(messages, prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    update_context_json(project_name, project)
    return upload_file(
        request=request,
        project_name=project_name,
        file_path="index.html",
        body=RequestBody(content=project.files[0].content),
        db=db,
        auth=auth,
    )


@games_router.get("/{project}")
def get_game_html(
    project: str,
    request: Request,
    count: bool = True,
    db: Session = Depends(get_db),
) -> Response:
    """
    Retrieve the HTML for a game project from GitHub.
    The endpoint attempts to fetch `index.html` under the project's directory.
    """

    try:
        content = github.get_file_content(project)
    except github.GithubFileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if count:
        # Update the number of opens for the game.
        game: Game | None = db.query(Game).filter(Game.project == project).first()
        if game is not None:
            game.num_opens += 1
            flag_modified(game, "num_opens")
            db.commit()

    return Response(content, media_type="text/html")


@games_router.get("/{project}/{file_path:path}")
def get_raw_file(
    project: str,
    file_path: str,
) -> Response:
    """
    Retrieve a raw file from a game project in GitHub.
    The endpoint attempts to fetch the specified file under the project's directory.
    """
    try:
        content = github.get_raw_file_content(project, file_path)
    except github.GithubFileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    media_type = mimetypes.guess_type(file_path)[0]
    return Response(content, media_type=media_type)


@file_router.get("/games")
def list_games(
    request: Request,
    sort_by: Literal["date_added", "date_modified", "hottest"] = Query("date_added"),
    search_query: str | None = Query(None, description="Search query for filtering game projects"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Search game projects.
    Optional query parameter 'sort_by' sorts by either "date_added", "date_modified", or "hottest".
    For "hottest", the sort order is num_opens DESC, then date_added DESC, then date_modified DESC.
    """
    page_size = 20
    query = db.query(Game)
    if search_query:
        search_query = f"%{search_query}%"
        query = query.filter(Game.project.ilike(search_query))

    if sort_by == "date_added":
        query = query.order_by(Game.date_added.desc())
    elif sort_by == "date_modified":
        query = query.order_by(Game.date_modified.desc())
    elif sort_by == "hottest":
        query = query.order_by(Game.num_opens.desc(), Game.date_added.desc(), Game.date_modified.desc())

    query = query.offset((page - 1) * page_size).limit(page_size)
    games = query.all()

    # Build API relative path for fetching HTML of each game.
    results: list[dict] = []
    for game in games:
        html_path = str(request.url_for("get_game_html", project=game.project).path)
        thumb_url = thumbs.get_thumb_url(f"{settings.APP_URL}{html_path}")
        results.append(
            {
                "project": game.project,
                "date_added": game.date_added,
                "date_modified": game.date_modified,
                "num_opens": game.num_opens,
                "html_path": html_path,
                "github_url": github.get_file_url(game.project),
                "thumb_url": thumb_url,
            }
        )
    return results


@file_router.delete("/project/{project_name}")
def delete_project(
    project_name: str = Path(..., description="Project name"),
    auth: str = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete a project
    - The project will be deleted from the database.
    - The project will be deleted from GitHub.
    """
    # Raise an error if the project does not exist.
    game: Game | None = db.query(Game).filter(Game.project == project_name).first()
    if game is None:
        raise HTTPException(status_code=400, detail="Project does not exist")

    try:
        github.delete_project(project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db.delete(game)
    db.commit()
    return {"status": "success"}


@file_router.get("/revert_project/{project_name}")
def revert_project(
    request: Request,
    project_name: str = Path(..., description="Project name"),
    _: str = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Revert a project to the last commit.
    - The project will be reverted from GitHub.
    """
    # Raise an error if the project does not exist.
    game: Game | None = db.query(Game).filter(Game.project == project_name).first()
    if game is None:
        raise HTTPException(status_code=400, detail="Project does not exist")

    try:
        github.revert_file_to_previous_commit(project_name, "index.html")
    except github.GithubFileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except github.GithubNoLastCommitError:
        raise HTTPException(status_code=400, detail="No previous commit found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Delete context.json if it exists.
    try:
        github.delete_file(project_name, "context.json")
    except github.GithubFileNotFoundError:
        pass

    # Update the modification timestamp in the database.
    game.date_modified = datetime.now(pytz.utc)
    flag_modified(game, "date_modified")
    db.commit()

    # Refresh the thumbnail.
    html_path = str(request.url_for("get_game_html", project=game.project).path)
    thumb_url = thumbs.get_thumb_url(f"{settings.APP_URL}{html_path}")
    background_tasks = BackgroundTasks()
    background_tasks.add_task(thumbs.refresh_thumb, f"{settings.APP_URL}{html_path}")
    response = JSONResponse(
        {
            "status": "success",
            "html_path": html_path,
            "thumb_url": thumb_url,
        }
    )
    response.background = background_tasks
    return response


router.include_router(ai_router)
router.include_router(file_router)
router.include_router(games_router)
router.include_router(admin_router)
