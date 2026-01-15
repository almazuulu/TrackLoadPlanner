"""Application configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Truck Load Planner API"
    app_version: str = "1.0.0"
    debug: bool = False

    # API settings
    api_v1_prefix: str = "/api/v1"

    # Optimization constraints
    max_orders_per_request: int = 25  # Maximum orders allowed in a single request

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
