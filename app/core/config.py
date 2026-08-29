"""Configuração da aplicação baseada em variáveis de ambiente."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Valores de configuração da API."""

    app_name: str = "Identidade Local API"
    app_env: str = "development"
    database_url: str = "sqlite:////data/identidade_local.db"
    jwt_secret_key: str = ""
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    password_reset_token_expire_minutes: int = 15
    cors_origins: str = "http://localhost:5173"
    viacep_base_url: str = "https://viacep.com.br/ws"
    viacep_timeout_seconds: float = 3.0
    viacep_rate_limit_requests: int = 10
    viacep_rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        """Retorna as origens CORS configuradas, sem valores vazios."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Obtém uma instância de configuração reutilizável."""
    return Settings()
