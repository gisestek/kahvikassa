from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, sourced from environment variables."""

    database_url: str = "postgresql+asyncpg://kahvikassa:kahvikassa@localhost:5432/kahvikassa"
    secret_key: str = "change-me-in-production"
    session_cookie_secure: bool = False

    # Kiosk sessions are kept short since this is a shared physical terminal.
    session_max_age_seconds: int = 60 * 10

    # Signal notifications (low stock, monthly fee charged) via a self-hosted
    # signal-cli-rest-api instance, linked as a secondary device to an
    # existing Signal account. Empty sender/group disables sending silently.
    signal_rest_api_url: str = "http://signal-cli:8080"
    signal_sender_number: str = ""
    signal_group_id: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
