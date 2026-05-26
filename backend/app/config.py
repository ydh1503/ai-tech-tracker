from __future__ import annotations

import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_ADMIN_TOKEN = "change-me-to-a-strong-secret-token"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 데이터베이스
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_tech_tracker"

    # 캐시
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # GitHub (선택)
    GITHUB_TOKEN: str = ""

    # 관리자 인증
    ADMIN_TOKEN: str = _DEFAULT_ADMIN_TOKEN

    # CORS (쉼표 구분 문자열 → list는 property로 변환)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # 환경
    ENV: str = "development"

    @model_validator(mode="after")
    def _check_admin_token(self) -> "Settings":
        if self.ADMIN_TOKEN == _DEFAULT_ADMIN_TOKEN:
            if self.ENV == "production":
                raise ValueError(
                    "ADMIN_TOKEN이 기본값입니다. 프로덕션 환경에서는 반드시 강력한 토큰으로 변경하세요."
                )
            logging.warning(
                "ADMIN_TOKEN이 기본값입니다. 프로덕션 환경에서는 반드시 변경하세요."
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


settings = Settings()
