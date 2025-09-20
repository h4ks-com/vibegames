import re


def sanitize_project_name(name: str) -> str:
    """
    Sanitize project name for use as subdomain/URL path.

    Rules:
    - Replace one or more spaces with single dash "-"
    - Replace any special characters (non-alphanumeric, non-dash) with underscore "_"
    - Keep alphanumeric characters and dashes as-is
    - Convert to lowercase for consistency

    Args:
        name: The project name to sanitize

    Returns:
        Sanitized project name suitable for subdomain/URL use
    """
    if not name:
        return ""

    # Convert to lowercase
    name = name.lower()

    # Replace one or more spaces with single dash
    name = re.sub(r"\s+", "-", name)

    # Replace any character that's not alphanumeric or dash with underscore
    name = re.sub(r"[^a-z0-9\-]", "_", name)

    # Remove leading/trailing dashes or underscores
    name = name.strip("-_")

    return name


def extract_subdomain(host: str, base_domain: str) -> str | None:
    """
    Extract subdomain from host header.

    Args:
        host: The host header value (e.g., "project.games.h4ks.com")
        base_domain: The base domain (e.g., "games.h4ks.com")

    Returns:
        The subdomain if found, None otherwise
    """
    if not host or not base_domain:
        return None

    # Remove port if present
    host = host.split(":")[0].lower()
    base_domain = base_domain.lower()

    # Check if host ends with base domain
    if not host.endswith(f".{base_domain}"):
        return None

    # Extract subdomain
    subdomain = host[: -len(f".{base_domain}")]

    # Validate subdomain (should not be empty and should be valid)
    if subdomain and re.match(r"^[a-z0-9\-_]+$", subdomain):
        return subdomain

    return None


def get_host_from_headers(headers: dict) -> str | None:
    """
    Extract host from request headers, checking common proxy headers.

    Args:
        headers: Request headers dictionary

    Returns:
        The host value if found
    """
    # Check common headers in order of preference
    host_headers = ["x-forwarded-host", "x-original-host", "x-real-host", "host"]

    for header_name in host_headers:
        # Try both lowercase and original case
        for key in [header_name.lower(), header_name]:
            if key in headers:
                host = headers[key]
                if isinstance(host, list):
                    host = host[0] if host else None
                if host:
                    # Take first value if comma-separated
                    return host.split(",")[0].strip()

    return None
