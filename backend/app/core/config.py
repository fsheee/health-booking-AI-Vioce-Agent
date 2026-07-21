import json

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env"}

    app_name: str = "Healthcare AI Voice Agent"
    debug: bool = False

    gemini_api_key: str
    assemblyai_api_key: str
    elevenlabs_api_key: str = ""
    deepgram_api_key: str = ""

    database_url: str

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3_driver(cls, v: str) -> str:
        # SQLAlchemy defaults "postgresql://" to psycopg2, which isn't installed.
        # Force the psycopg (v3) driver instead.
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return [v]
        return v

    backend_url: str = "http://localhost:8000"

    # SMTP / Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@healthcare-clinic.com"
    smtp_from_name: str = "Healthcare Clinic"
    smtp_use_tls: bool = True


settings = Settings()
