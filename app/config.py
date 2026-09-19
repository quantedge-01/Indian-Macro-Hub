"""Runtime configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("APP_ENV", "development")
    database: str | None = os.getenv("INDIAN_MACRO_HUB_DATABASE")
    seed_demo_data: bool = _boolean("SEED_DEMO_DATA", True)
    cors_origins: tuple[str, ...] = tuple(
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()
    )

    @property
    def database_path(self) -> str | None:
        return str(Path(self.database).expanduser()) if self.database else None


settings = Settings()
