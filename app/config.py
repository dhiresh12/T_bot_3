from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    app_name: str = "Xio PayPlus"
    environment: str = "development"
    secret_key: str = ""
    ads_provider: str = "admob"
    host: str = "0.0.0.0"
    port: int = 5000
    app_version: str = "1.0.0"
    min_supported_version: str = "0.9.0"


def load_config() -> AppConfig:
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY must be set in production.")
    return AppConfig(
        app_name=os.getenv("APP_NAME", "Xio PayPlus"),
        environment=os.getenv("APP_ENV", "development"),
        secret_key=secret_key,
        ads_provider=os.getenv("ADS_PROVIDER", "admob"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
    )
