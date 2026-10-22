import os
from pathlib import Path


class Settings:
    """Configuración leída del entorno."""

    @property
    def auth_service_url(self) -> str:
        return os.environ.get("REPORTS_AUTH_SERVICE_URL", "http://localhost:8000").rstrip("/")

    @property
    def transactions_service_url(self) -> str:
        return os.environ.get("REPORTS_TRANSACTIONS_SERVICE_URL", "http://localhost:8001").rstrip("/")

    @property
    def budgets_service_url(self) -> str:
        return os.environ.get("REPORTS_BUDGETS_SERVICE_URL", "http://localhost:8002").rstrip("/")

    @property
    def database_url(self) -> str:
        return os.environ.get("REPORTS_DATABASE_URL", "sqlite:///./reports.db")

    @property
    def storage_dir(self) -> Path:
        return Path(os.environ.get("REPORTS_STORAGE_DIR", "./generated_reports"))


settings = Settings()
