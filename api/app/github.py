import base64
import re
from functools import lru_cache

import requests

from app.settings import settings


class GithubFileNotFoundError(Exception):
    """Custom exception for file not found in GitHub repository."""

    pass


@lru_cache
def get_repo_owner_and_name(repo_url: str) -> tuple[str, str]:
    repo_url = settings.GITHUB_REPOSITORY
    repo_owner_match = re.search(r"github\.com/([^/]+)/", repo_url)
    repo_name_match = re.search(r"github\.com/[^/]+/(.+)", repo_url)
    if not repo_owner_match or not repo_name_match:
        raise ValueError("Invalid GitHub repository URL")
    repo_owner = repo_owner_match.group(1)
    repo_name = repo_name_match.group(1).removesuffix(".git")

    return repo_owner, repo_name


def update_or_create_file(path: str, content: str, project: str) -> None:
    repo_owner, repo_name = get_repo_owner_and_name(settings.GITHUB_REPOSITORY)
    # Construct the GitHub API URL.
    # Files will reside under: {GAMES_PATH}/{project}/{path}
    api_url = (
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{settings.PROJECTS_PATH}/{project}/{path}"
    )

    headers = {"Authorization": f"token {settings.GITHUB_API_TOKEN}"}
    get_resp = requests.get(api_url, headers=headers)

    # Prepare content for commit (GitHub requires the content in base64)
    content_bytes = content.encode()
    content_encoded = base64.b64encode(content_bytes).decode()

    commit_message = "Update file via API"
    data = {"message": commit_message, "content": content_encoded}

    if get_resp.status_code == 200:
        file_info = get_resp.json()
        data["sha"] = file_info.get("sha")
    elif get_resp.status_code != 404:
        # If it's neither found nor a clear "not found", something is wrong.
        get_resp.raise_for_status()

    put_resp = requests.put(api_url, json=data, headers=headers)
    put_resp.raise_for_status()


def get_file_content(project: str, path: str | None = None) -> str:
    repo_owner, repo_name = get_repo_owner_and_name(settings.GITHUB_REPOSITORY)
    base_url = (
        f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/{settings.PROJECTS_PATH}/{project}"
    )

    path = path or "index.html"
    base_url = f"{base_url}/index.html"
    resp = requests.get(base_url)
    if resp.status_code == 200:
        return resp.text
    else:
        raise GithubFileNotFoundError(f"File not found: {base_url}")
