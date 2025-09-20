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
