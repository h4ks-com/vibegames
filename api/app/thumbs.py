import requests

from app.settings import settings


def get_thumb_url(game_url: str) -> str:
    return f"{settings.CAPTURE_API_URL}/capture?url={game_url}&format=webp&length=4"


def refresh_thumb(game_url: str, force_recreate=True) -> None:
    """Refreshes the thumbnail for a game URL."""
    api_url = get_thumb_url(game_url)
    if force_recreate:
        api_url += "&nocache"
    headers = {"Authorization": f"Bearer {settings.CAPTURE_API_KEY}"}
    resp = requests.get(api_url, headers=headers)
    resp.raise_for_status()
