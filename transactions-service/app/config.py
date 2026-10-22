import os


class Settings:
    """Configuración leída del entorno."""

    @property
    def auth_service_url(self) -> str:
        return os.environ.get("TRANSACTIONS_AUTH_SERVICE_URL", "http://localhost:8000").rstrip("/")

    @property
    def database_url(self) -> str:
        return os.environ.get("TRANSACTIONS_DATABASE_URL", "sqlite:///./transactions.db")


settings = Settings()