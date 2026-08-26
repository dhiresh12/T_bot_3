from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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


@dataclass
class AdCompletion:
    ad_unit_id: str
    user_id: int
    provider: str
    reward_coins: int
    reward_money: float
    timestamp: float
    ip_hash: str = ""
    device_hash: str = ""
    completion_seconds: float = 0.0
    provider_data: Dict[str, Any] = field(default_factory=dict)
    duplicate: bool = False
    fraud_score: int = 0


class AdsManager:
    def __init__(self, provider: str = "admob") -> None:
        provider = provider or os.getenv("ADS_PROVIDER", "admob")
        self.provider = provider
        self.config = self._default_config(provider)
        self._completed_ads: Dict[str, AdCompletion] = {}
        self._user_daily: Dict[str, Dict[str, Any]] = {}
        self._blocked_ips: set = set()
        self._blocked_devices: set = set()
        self._min_completion_seconds = 3
        self._max_completion_seconds = 120
        self._fraud_threshold = 3

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

    def _hash(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    def get_providers(self) -> List[Dict[str, Any]]:
        return [
            {"provider": "admob", "priority": 1, "status": "active"},
            {"provider": "adsense", "priority": 2, "status": "active"},
            {"provider": "adinplay", "priority": 3, "status": "active"},
        ]

    def get_next_provider(self, failed_provider: Optional[str] = None) -> str:
        providers = self.get_providers()
        for p in providers:
            if p["provider"] == failed_provider:
                continue
            return p["provider"]
        return "admob"

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

    def block_ip(self, ip_hash: str) -> None:
        self._blocked_ips.add(ip_hash)

    def block_device(self, device_hash: str) -> None:
        self._blocked_devices.add(device_hash)

    def is_blocked(self, ip_hash: str, device_hash: str) -> bool:
        return ip_hash in self._blocked_ips or device_hash in self._blocked_devices

    def _fraud_score(self, completion: AdCompletion) -> int:
        score = 0
        if completion.completion_seconds < self._min_completion_seconds:
            score += 2
        if completion.completion_seconds > self._max_completion_seconds:
            score += 1
        if not completion.ip_hash:
            score += 1
        if not completion.device_hash:
            score += 1
        return score

    def verify_ad_completion(
        self,
        ad_unit_id: str,
        user_id: int,
        provider_data: Optional[Dict[str, Any]] = None,
        ip_hash: str = "",
        device_hash: str = "",
        completion_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        if ad_unit_id in self._completed_ads:
            return {
                "valid": False,
                "reason": "duplicate",
                "reward_coins": 0,
                "reward_money": 0.0,
            }

        if self.is_blocked(ip_hash, device_hash):
            return {
                "valid": False,
                "reason": "blocked",
                "reward_coins": 0,
                "reward_money": 0.0,
            }

        today = time.strftime("%Y-%m-%d")
        key = f"{user_id}:{today}"
        user_stats = self._user_daily.setdefault(key, {"ads": 0, "first_ts": time.time()})
        if user_stats["ads"] >= self.config.daily_limit:
            return {
                "valid": False,
                "reason": "daily_limit",
                "reward_coins": 0,
                "reward_money": 0.0,
            }

        completion = AdCompletion(
            ad_unit_id=ad_unit_id,
            user_id=user_id,
            provider=self.config.provider,
            reward_coins=self._random_coins(),
            reward_money=self.config.reward_per_ad * (self.config.user_share_percent / 100),
            timestamp=time.time(),
            ip_hash=ip_hash,
            device_hash=device_hash,
            completion_seconds=completion_seconds,
            provider_data=provider_data or {},
        )
        completion.fraud_score = self._fraud_score(completion)
        if completion.fraud_score >= self._fraud_threshold:
            completion.duplicate = True
            self.block_ip(ip_hash)
            self.block_device(device_hash)
            return {
                "valid": False,
                "reason": "fraud",
                "reward_coins": 0,
                "reward_money": 0.0,
            }

        self._completed_ads[ad_unit_id] = completion
        user_stats["ads"] += 1
        return {
            "valid": True,
            "reason": "completed",
            "reward_coins": completion.reward_coins,
            "reward_money": round(completion.reward_money, 4),
            "ad_unit_id": ad_unit_id,
            "provider": completion.provider,
        }

    def get_daily_stats(self, user_id: int) -> Dict[str, Any]:
        today = time.strftime("%Y-%m-%d")
        ads_today = sum(
            1
            for ad in self._completed_ads.values()
            if ad.user_id == user_id and time.strftime("%Y-%m-%d", time.localtime(ad.timestamp)) == today
        )
        return {
            "user_id": user_id,
            "date": today,
            "ads_completed": ads_today,
            "daily_limit": self.config.daily_limit,
            "remaining": max(0, self.config.daily_limit - ads_today),
            "total_earnings": sum(
                ad.reward_money
                for ad in self._completed_ads.values()
                if ad.user_id == user_id and time.strftime("%Y-%m-%d", time.localtime(ad.timestamp)) == today
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

    def generate_ad_unit_id(self, user_id: int, ad_index: int) -> str:
        return f"{self.config.provider}:{user_id}:{ad_index}:{int(time.time())}"

    def verify_callback_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def get_admin_stats(self) -> Dict[str, Any]:
        today = time.strftime("%Y-%m-%d")
        today_ads = [
            ad for ad in self._completed_ads.values()
            if time.strftime("%Y-%m-%d", time.localtime(ad.timestamp)) == today
        ]
        total_users = len({ad.user_id for ad in today_ads})
        total_revenue = sum(ad.reward_money for ad in today_ads)
        return {
            "date": today,
            "ads_completed": len(today_ads),
            "unique_users": total_users,
            "total_revenue": round(total_revenue, 4),
            "provider": self.config.provider,
            "blocked_ips": len(self._blocked_ips),
            "blocked_devices": len(self._blocked_devices),
        }
