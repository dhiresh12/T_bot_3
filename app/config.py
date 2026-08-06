from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    app_name: str = "Xio PayPlus"
    environment: str = "development"
    secret_key: str = "dev-secret"
    ads_provider: str = "admob"
    host: str = "0.0.0.0"
    port: int = 5000


def load_config() -> AppConfig:
    return AppConfig(
        app_name=os.getenv("APP_NAME", "Xio PayPlus"),
        environment=os.getenv("APP_ENV", "development"),
        secret_key=os.getenv("SECRET_KEY", "dev-secret"),
        ads_provider=os.getenv("ADS_PROVIDER", "admob"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
    )
