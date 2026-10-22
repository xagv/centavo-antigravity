import os


class Settings:
    """Configuración leída del entorno."""

    @property
    def auth_service_url(self) -> str:
        return os.environ.get("NOTIFICATIONS_AUTH_SERVICE_URL", "http://localhost:8000").rstrip("/")

    @property
    def budgets_service_url(self) -> str:
        return os.environ.get("NOTIFICATIONS_BUDGETS_SERVICE_URL", "http://localhost:8002").rstrip("/")

    @property
    def database_url(self) -> str:
        return os.environ.get("NOTIFICATIONS_DATABASE_URL", "sqlite:///./notifications.db")


settings = Settings()
