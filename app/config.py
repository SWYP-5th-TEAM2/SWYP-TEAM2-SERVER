from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="SWYP TEAM2 SERVER", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    database_url: str = Field(alias="DATABASE_URL")

    # ===== JWT =====
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=14,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )

    # ===== Redis =====
    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str = Field(alias="REDIS_PASSWORD")

    # ===== Kakao OAuth =====
    kakao_client_id: str = Field(alias="KAKAO_CLIENT_ID")
    kakao_redirect_uri: str = Field(alias="KAKAO_REDIRECT_URI")
    kakao_client_secret: str = Field(alias="KAKAO_CLIENT_SECRET")
    kakao_local_rest_api_key: str | None = Field(default=None, alias="KAKAO_LOCAL_REST_API_KEY")
    naver_local_client_id: str | None = Field(default=None, alias="NAVER_LOCAL_CLIENT_ID")
    naver_local_client_secret: str | None = Field(default=None, alias="NAVER_LOCAL_CLIENT_SECRET")


    # ===== Firebase FCM =====
    firebase_push_enabled: bool = Field(default=False, alias="FIREBASE_PUSH_ENABLED")
    firebase_project_id: str | None = Field(default=None, alias="FIREBASE_PROJECT_ID")
    firebase_credentials_path: str | None = Field(default=None, alias="FIREBASE_CREDENTIALS_PATH")

    # ===== Google OAuth =====
    google_client_id: str = Field(alias="GOOGLE_CLIENT_ID")
    google_redirect_uri: str = Field(alias="GOOGLE_REDIRECT_URI")
    google_client_secret: str = Field(alias="GOOGLE_CLIENT_SECRET")

    # ===== Apple OAuth =====
    apple_team_id: str | None = Field(default=None, alias="APPLE_TEAM_ID")
    apple_client_id: str | None = Field(default=None, alias="APPLE_CLIENT_ID")
    apple_key_id: str | None = Field(default=None, alias="APPLE_KEY_ID")
    apple_private_key: str | None = Field(default=None, alias="APPLE_PRIVATE_KEY")
    apple_redirect_uri: str | None = Field(default=None, alias="APPLE_REDIRECT_URI")

    # ===== Azure Blob Storage =====
    azure_storage_connection_string: str = Field(alias="AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_container_name: str = Field(alias="AZURE_STORAGE_CONTAINER_NAME")
    max_image_size_mb: int = Field(
        default=5,
        gt=0,
        alias="MAX_IMAGE_SIZE_MB",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
