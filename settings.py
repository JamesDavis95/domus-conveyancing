from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # App
    APP_ENV: str = "dev"
    SECRET_KEY: str = "dev-secret"

    # Core services
    DATABASE_URL: str = "postgresql+psycopg2://postgres:dev@postgres:5432/postgres"
    REDIS_URL: str = "redis://redis:6379/0"

    # S3 / MinIO
    S3_ENDPOINT: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "domus"
    S3_REGION: str = "us-east-1"
    S3_PATH_STYLE: bool = True

    # AV
    AV_SCAN: bool = True
    CLAMAV_HOST: str = "clamav"
    CLAMAV_PORT: int = 3310

    # Auth (OIDC/JWT)
    AUTH_ENABLED: bool = False
    OIDC_AUTHORITY: Optional[str] = None  # e.g., https://login.microsoftonline.com/<tenant>/v2.0
    OIDC_JWKS_URI: Optional[str] = None   # optional override, else discovered from authority
    OIDC_AUDIENCE: Optional[str] = None   # API client ID / audience
    OIDC_ISSUER: Optional[str] = None     # expected issuer; if None, use discovery issuer
    OIDC_ALLOWED_ALGS: str = "RS256"      # comma-separated list

    # Metrics
    METRICS_ENABLED: bool = True

settings = Settings()
