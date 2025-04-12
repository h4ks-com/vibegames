from datetime import datetime
from typing import Literal

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app import github
from app.auth import get_api_key
from app.database import get_db
from app.models import Game

router = APIRouter(tags=["File management"], prefix="/api")


@router.put("/{project}/{file_path:path}")
def update_file(
    project: str,
    file_path: str,
    content: str,
    _: str = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> dict:
    """
    Update or create a file inside a project folder in GitHub.
    - If the project does not exist in the database, create a new row.
    - If it exists, update the modification timestamp.
    """
    try:
        github.update_or_create_file(file_path, content, project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Update database entry.
    game: Game | None = db.query(Game).filter(Game.project == project).first()
    now = datetime.now(pytz.utc)
    if game is None:
        game = Game(project=project, date_added=now, date_modified=now, num_opens=0)
        db.add(game)
    else:
        game.date_modified = now
        flag_modified(game, "date_modified")
    db.commit()
    return {"status": "success"}


@router.get("/game/{project}")
def get_game_html(project: str, db: Session = Depends(get_db)) -> Response:
    """
    Retrieve the HTML for a game project from GitHub.
    The endpoint attempts to fetch `index.html` under the project's directory.
    """
    try:
        content = github.get_file_content(project)
    except github.GithubFileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Update the number of opens for the game.
    game: Game | None = db.query(Game).filter(Game.project == project).first()
    if game is not None:
        game.num_opens += 1
        flag_modified(game, "num_opens")
        db.commit()

    return Response(content, media_type="text/html")


@router.get("/api/games")
def list_games(
    sort_by: Literal["date_added", "date_modified", "hottest"] = Query("date_added"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List all game projects.
    Optional query parameter 'sort_by' sorts by either "date_added", "date_modified", or "hottest".
    For "hottest", the sort order is num_opens DESC, then date_added DESC, then date_modified DESC.
    """
    query = db.query(Game)
    if sort_by == "date_added":
        query = query.order_by(Game.date_added.desc())
    elif sort_by == "date_modified":
        query = query.order_by(Game.date_modified.desc())
    elif sort_by == "hottest":
        query = query.order_by(Game.num_opens.desc(), Game.date_added.desc(), Game.date_modified.desc())

    games = query.all()
    # Build API relative path for fetching HTML of each game.
    results: list[dict] = []
    for game in games:
        results.append(
            {
                "project": game.project,
                "date_added": game.date_added,
                "date_modified": game.date_modified,
                "num_opens": game.num_opens,
                "html_path": f"/api/game/{game.project}",
            }
        )
    return results
