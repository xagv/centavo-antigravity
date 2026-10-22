import os


class Settings:
    """Configuración leída del entorno. Sin valores por defecto para secretos."""

    @property
    def jwt_secret(self) -> str:
        secret = os.environ.get("AUTH_JWT_SECRET", "")
        if len(secret) < 32:
            raise RuntimeError("AUTH_JWT_SECRET debe definirse con al menos 32 caracteres")
        return secret

    @property
    def database_url(self) -> str:
        return os.environ.get("AUTH_DATABASE_URL", "sqlite:///./auth.db")

    @property
    def token_ttl_minutes(self) -> int:
        return int(os.environ.get("AUTH_TOKEN_TTL_MINUTES", "60"))


settings = Settings()
