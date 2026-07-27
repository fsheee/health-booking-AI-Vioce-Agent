import json
import os

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

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
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    cors_origins: list[str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                if "," in v:
                    return [o.strip() for o in v.split(",") if o.strip()]
                return [v]
        return v

    frontend_url: str = ""
    vercel_frontend_url: str = ""

    @model_validator(mode="after")
    def _add_extra_origins(self):
        extra = []
        if self.frontend_url:
            extra.append(self.frontend_url.rstrip("/"))
        if self.vercel_frontend_url:
            extra.append(f"https://{self.vercel_frontend_url}")
        if os.environ.get("VERCEL") == "1":
            for key in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_GIT_PULL_REQUEST_URL"):
                url = os.environ.get(key)
                if url:
                    extra.append(f"https://{url}")
        if extra:
            self.cors_origins = list(set(self.cors_origins + extra))
        return self

    backend_url: str = "http://127.0.0.1:8000"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@healthcare-clinic.com"
    smtp_from_name: str = "Healthcare Clinic"
    smtp_use_tls: bool = True


settings = Settings()
