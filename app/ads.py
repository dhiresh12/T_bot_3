from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AdConfig:
    provider: str
    reward_per_ad: float      # money (in rupees) the USER earns per completed ad
    reward_currency: str
    daily_limit: int
    cooldown_seconds: int
    user_share_percent: int   # % of ad revenue shared with the user (40-55%)
    reward_coins_min: int     # random coin range per completed ad
    reward_coins_max: int
    ads_per_completion: int   # how many back-to-back ads == 1 completion reward


class AdsManager:
    def __init__(self, provider: str = "admob") -> None:
        # Allow override via env so the deploy can switch providers without code changes.
        provider = provider or os.getenv("ADS_PROVIDER", "admob")
        self.provider = provider
        self.config = self._default_config(provider)

    def _default_config(self, provider: str) -> AdConfig:
        if provider.lower() in ("adsense", "google_adsense", "googleada"):
            return AdConfig(
                provider="adsense",
                reward_per_ad=0.002,          # ₹0.002 per completed ad
                reward_currency="rupees",
                daily_limit=15,
                cooldown_seconds=60,
                user_share_percent=50,        # 50% of ad revenue shared with users
                reward_coins_min=50,
                reward_coins_max=500,
                ads_per_completion=2,         # 2 back-to-back ads = 1 completion
            )
        if provider.lower() == "adinplay":
            return AdConfig(
                provider="adinplay",
                reward_per_ad=0.002,
                reward_currency="rupees",
                daily_limit=15,
                cooldown_seconds=60,
                user_share_percent=40,
                reward_coins_min=50,
                reward_coins_max=500,
                ads_per_completion=2,
            )
        # Default to admob.
        return AdConfig(
            provider="admob",
            reward_per_ad=0.002,
            reward_currency="rupees",
            daily_limit=15,
            cooldown_seconds=60,
            user_share_percent=45,
            reward_coins_min=50,
            reward_coins_max=500,
            ads_per_completion=2,
        )

    def get_config(self) -> Dict[str, Any]:
        return {
            "provider": self.config.provider,
            "reward_per_ad": self.config.reward_per_ad,
            "reward_currency": self.config.reward_currency,
            "daily_limit": self.config.daily_limit,
            "cooldown_seconds": self.config.cooldown_seconds,
            "user_share_percent": self.config.user_share_percent,
            "reward_coins_min": self.config.reward_coins_min,
            "reward_coins_max": self.config.reward_coins_max,
            "ads_per_completion": self.config.ads_per_completion,
        }

    def build_widget(self) -> Dict[str, Any]:
        return {
            "type": "rewarded-ad",
            "provider": self.config.provider,
            "label": "Watch Ad",
            "daily_limit": self.config.daily_limit,
            "reward_per_ad": self.config.reward_per_ad,
            "user_share_percent": self.config.user_share_percent,
        }

