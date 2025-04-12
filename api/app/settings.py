from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GITHUB_API_TOKEN: str
    GITHUB_REPOSITORY: str
    PROJECTS_PATH: str
    API_KEYS: list[str]
    DB_PATH: str
    PORT: int = 8080
    RELOAD: bool = False
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
