from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AdConfig:
    provider: str
    reward_per_ad: float
    reward_currency: str
    daily_limit: int
    cooldown_seconds: int
    user_share_percent: int
    reward_coins_min: int
    reward_coins_max: int
    ads_per_completion: int


class AdsManager:
    def __init__(self, provider: str = "admob") -> None:
        provider = provider or os.getenv("ADS_PROVIDER", "admob")
        self.provider = provider
        self.config = self._default_config(provider)
        self._completed_ads: Dict[str, Dict[str, Any]] = {}

    def _default_config(self, provider: str) -> AdConfig:
        if provider.lower() in ("adsense", "google_adsense", "googleada"):
            return AdConfig(
                provider="adsense",
                reward_per_ad=0.002,
                reward_currency="rupees",
                daily_limit=15,
                cooldown_seconds=60,
                user_share_percent=50,
                reward_coins_min=50,
                reward_coins_max=500,
                ads_per_completion=2,
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

    def generate_ad_unit_id(self, user_id: int, ad_index: int) -> str:
        return f"{self.config.provider}:{user_id}:{ad_index}:{int(time.time())}"

    def verify_ad_completion(self, ad_unit_id: str, user_id: int, provider_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if ad_unit_id in self._completed_ads:
            return {
                "valid": False,
                "reason": "duplicate",
                "reward_coins": 0,
                "reward_money": 0.0,
            }

        reward_coins = 0
        reward_money = 0.0

        if self.config.provider == "admob":
            reward_coins = self._random_coins()
            reward_money = self.config.reward_per_ad * (self.config.user_share_percent / 100)
        elif self.config.provider == "adsense":
            reward_coins = self._random_coins()
            reward_money = self.config.reward_per_ad * (self.config.user_share_percent / 100)
        elif self.config.provider == "adinplay":
            reward_coins = self._random_coins()
            reward_money = self.config.reward_per_ad * (self.config.user_share_percent / 100)

        self._completed_ads[ad_unit_id] = {
            "user_id": user_id,
            "reward_coins": reward_coins,
            "reward_money": reward_money,
            "timestamp": time.time(),
            "provider_data": provider_data or {},
        }

        return {
            "valid": True,
            "reason": "completed",
            "reward_coins": reward_coins,
            "reward_money": round(reward_money, 4),
            "ad_unit_id": ad_unit_id,
        }

    def get_daily_stats(self, user_id: int) -> Dict[str, Any]:
        today = time.strftime("%Y-%m-%d")
        ads_today = sum(
            1
            for ad in self._completed_ads.values()
            if ad["user_id"] == user_id and time.strftime("%Y-%m-%d", time.localtime(ad["timestamp"])) == today
        )
        return {
            "user_id": user_id,
            "date": today,
            "ads_completed": ads_today,
            "daily_limit": self.config.daily_limit,
            "remaining": max(0, self.config.daily_limit - ads_today),
            "total_earnings": sum(
                ad["reward_money"]
                for ad in self._completed_ads.values()
                if ad["user_id"] == user_id and time.strftime("%Y-%m-%d", time.localtime(ad["timestamp"])) == today
            ),
        }

    def _random_coins(self) -> int:
        import random
        return random.randint(self.config.reward_coins_min, self.config.reward_coins_max)

    def build_verification_payload(self, user_id: int, ad_index: int) -> Dict[str, Any]:
        ad_unit_id = self.generate_ad_unit_id(user_id, ad_index)
        return {
            "ad_unit_id": ad_unit_id,
            "user_id": user_id,
            "provider": self.config.provider,
            "timestamp": int(time.time()),
            "reward_coins": self._random_coins(),
            "reward_money": round(self.config.reward_per_ad * (self.config.user_share_percent / 100), 4),
        }

    def verify_callback_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
