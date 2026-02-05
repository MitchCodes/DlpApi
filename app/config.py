from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_PATH = Path("config.json")


class _EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DLP_API_",
        case_sensitive=False,
    )

    auth_token: str | None = None
    download_root: str | None = None
    log_level: str | None = None
    config_file: str | None = None


@dataclass(frozen=True)
class AppSettings:
    auth_token: str | None
    download_root: Path
    log_level: str
    config_file: Path


def _load_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logging.getLogger(__name__).exception("Failed to read config file: %s", path)
        return {}


def load_settings() -> AppSettings:
    env = _EnvSettings()
    config_path = Path(env.config_file) if env.config_file else DEFAULT_CONFIG_PATH
    file_data = _load_config_file(config_path)

    auth_token = env.auth_token or file_data.get("auth_token")
    download_root = Path(env.download_root or file_data.get("download_root") or "downloads")
    log_level = (env.log_level or file_data.get("log_level") or "INFO").upper()

    return AppSettings(
        auth_token=auth_token,
        download_root=download_root,
        log_level=log_level,
        config_file=config_path,
    )
