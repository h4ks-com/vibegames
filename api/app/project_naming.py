import re

from sqlalchemy.orm import Session

from app.models import Game


def sanitize_project_name(project_name: str) -> str:
    """
    Sanitize project name for subdomain/URL use.

    Converts to lowercase, replaces spaces with dashes,
    special characters with underscores, and trims edges.
    """
    if not project_name:
        return ""

    sanitized = project_name.lower()
    sanitized = re.sub(r"\s+", "-", sanitized)
    sanitized = re.sub(r"[^a-z0-9\-]", "_", sanitized)
    return sanitized.strip("-_")


def extract_subdomain(host: str, base_domain: str) -> str | None:
    """Extract subdomain from host header if valid."""
    if not host or not base_domain:
        return None

    clean_host = host.split(":")[0].lower()
    clean_domain = base_domain.lower()

    if not clean_host.endswith(f".{clean_domain}"):
        return None

    subdomain = clean_host[: -len(f".{clean_domain}")]

    if subdomain and re.match(r"^[a-z0-9\-_]+$", subdomain):
        return subdomain

    return None


def get_host_from_headers(headers: dict[str, str | list[str]]) -> str | None:
    """Extract host from request headers, checking proxy headers first."""
    proxy_headers = ["x-forwarded-host", "x-original-host", "x-real-host", "host"]

    for header_name in proxy_headers:
        for header_key in [header_name.lower(), header_name]:
            if header_key in headers:
                header_value = headers[header_key]
                if isinstance(header_value, list):
                    host_value = header_value[0] if header_value else None
                else:
                    host_value = header_value

                if host_value:
                    return host_value.split(",")[0].strip()

    return None


def find_project_by_name_case_insensitive(db: Session, project_name: str) -> Game | None:
    """
    Find project with case-insensitive sanitized lookup and backwards compatibility.

    Always sanitizes input before matching for consistency.
    """

    sanitized_input = sanitize_project_name(project_name)

    exact_match = db.query(Game).filter(Game.project == sanitized_input).first()
    if exact_match:
        return exact_match

    # Backwards compatibility: check if any existing project sanitizes to our input
    all_projects = db.query(Game).all()
    for project in all_projects:
        if sanitize_project_name(project.project) == sanitized_input:
            return project

    return None
