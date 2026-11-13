from typing import Any

from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    GITHUB_API_TOKEN: str
    GITHUB_REPOSITORY: str
    PROJECTS_PATH: str
    API_KEYS: list[str] | str
    DB_PATH: str
    APP_URL: str = "http://localhost:8088"
    GPT4F_API_URL: str = "https://g4f.cloud.mattf.one"
    CAPTURE_API_URL: str
    CAPTURE_API_KEY: str
    PORT: int = 8080
    RELOAD: bool = False
    DEBUG: bool = False
    ENABLE_SUBDOMAINS: bool = False
    BASE_DOMAIN: str = "games.h4ks.com"

    # Logto (https://auth.h4ks.com). Leave LOGTO_CLIENT_ID empty to disable user login.
    LOGTO_ISSUER: str = "https://auth.h4ks.com/oidc"
    LOGTO_CLIENT_ID: str = ""
    LOGTO_CLIENT_SECRET: str = ""
    LOGTO_REDIRECT_URI: str = ""
    LOGTO_SCOPE: str = "openid profile"
    SESSION_COOKIE_NAME: str = "vg_session"
    # Set to BASE_DOMAIN so every project subdomain shares one login.
    # Empty means host-only cookie (correct for localhost).
    SESSION_COOKIE_DOMAIN: str = ""
    SESSION_TTL_DAYS: int = 30

    # Rows API (see docs/rows-api.md). The app id always comes from the subdomain.
    OBBY_ENABLED: bool = True
    # Used instead of a subdomain when ENABLE_SUBDOMAINS is off (local dev and tests).
    OBBY_DEV_APP: str = "dev"
    OBBY_MAX_VALUE_BYTES: int = 8192
    OBBY_MAX_KEYS: int = 64
    OBBY_MAX_BYTES: int = 131072
    OBBY_MAX_PUBLIC_ROWS: int = 5000
    OBBY_WRITES_PER_MINUTE: int = 60

    # API keys can be a single string or a comma-separated list
    @model_validator(mode="before")
    @classmethod
    def validate_api_keys(cls, model: dict[str, Any]) -> dict[str, Any]:
        v = model.get("API_KEYS")
        if v is not None:
            if v.strip().startswith("[") and v.strip().endswith("]"):
                api_keys = v
            elif "," in v:
                api_keys = [key.strip() for key in v.split(",")]
            else:
                api_keys = [v.strip()]
            model["API_KEYS"] = api_keys
        return model

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
