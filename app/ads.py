from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AdConfig:
    provider: str
    reward_per_ad: float
    reward_currency: str
    daily_limit: int
    cooldown_seconds: int


class AdsManager:
    def __init__(self, provider: str = "admob") -> None:
        self.provider = provider
        self.config = self._default_config(provider)

    def _default_config(self, provider: str) -> AdConfig:
        if provider.lower() == "adinplay":
            return AdConfig(provider="adinplay", reward_per_ad=0.002, reward_currency="rupees", daily_limit=15, cooldown_seconds=60)
        return AdConfig(provider="admob", reward_per_ad=0.002, reward_currency="rupees", daily_limit=15, cooldown_seconds=60)

    def get_config(self) -> Dict[str, Any]:
        return {
            "provider": self.config.provider,
            "reward_per_ad": self.config.reward_per_ad,
            "reward_currency": self.config.reward_currency,
            "daily_limit": self.config.daily_limit,
            "cooldown_seconds": self.config.cooldown_seconds,
        }

    def build_widget(self) -> Dict[str, Any]:
        return {
            "type": "rewarded-ad",
            "provider": self.config.provider,
            "label": "Watch Ad",
            "daily_limit": self.config.daily_limit,
        }
