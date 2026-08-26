"""Premium subscription tiers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PremiumTier:
    tier_id: str
    name: str
    price_inr: float
    duration_days: int
    benefits: Dict[str, Any]
    active: bool = True


class PremiumService:
    def __init__(self) -> None:
        self.tiers: Dict[str, PremiumTier] = {}
        self.user_subscriptions: Dict[int, Dict[str, Any]] = {}
        self._load_default_tiers()

    def _load_default_tiers(self) -> None:
        defaults = [
            PremiumTier(
                tier_id="no_ads",
                name="No Ads",
                price_inr=29.0,
                duration_days=30,
                benefits={"no_ads": True, "bonus_coins": 0, "spin_boost": 1},
            ),
            PremiumTier(
                tier_id="double_rewards",
                name="Double Rewards",
                price_inr=49.0,
                duration_days=30,
                benefits={"no_ads": True, "bonus_coins": 2, "spin_boost": 2},
            ),
            PremiumTier(
                tier_id="exclusive",
                name="Exclusive Crate Access",
                price_inr=99.0,
                duration_days=30,
                benefits={"no_ads": True, "bonus_coins": 3, "spin_boost": 3, "exclusive_crates": True},
            ),
        ]
        for t in defaults:
            self.tiers[t.tier_id] = t

    def get_tiers(self) -> List[Dict[str, Any]]:
        return [
            {
                "tier_id": t.tier_id,
                "name": t.name,
                "price_inr": t.price_inr,
                "duration_days": t.duration_days,
                "benefits": t.benefits,
                "active": t.active,
            }
            for t in self.tiers.values()
            if t.active
        ]

    def get_user_subscription(self, user_id: int) -> Dict[str, Any]:
        sub = self.user_subscriptions.get(user_id)
        if not sub:
            return {"active": False, "tier_id": None, "expires_at": None}
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if sub.get("expires_at") and now.isoformat() > sub["expires_at"]:
            sub["active"] = False
        return sub

    def purchase_subscription(self, user_id: int, tier_id: str, payment_ref: str = "") -> tuple[bool, str, Dict[str, Any]]:
        tier = self.tiers.get(tier_id)
        if not tier or not tier.active:
            return False, "Invalid tier", {}
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires = (now + timedelta(days=tier.duration_days)).isoformat()
        self.user_subscriptions[user_id] = {
            "user_id": user_id,
            "tier_id": tier_id,
            "name": tier.name,
            "price_inr": tier.price_inr,
            "purchased_at": now.isoformat(),
            "expires_at": expires,
            "active": True,
            "payment_ref": payment_ref,
            "benefits": tier.benefits,
        }
        return True, f"Subscribed to {tier.name}!", {"tier_id": tier_id, "expires_at": expires, "benefits": tier.benefits}

    def get_benefits(self, user_id: int) -> Dict[str, Any]:
        sub = self.get_user_subscription(user_id)
        if not sub.get("active"):
            return {"active": False, "bonus_coins": 1, "spin_boost": 1, "no_ads": False}
        return {
            "active": True,
            "tier_id": sub.get("tier_id"),
            "name": sub.get("name"),
            "bonus_coins": sub.get("benefits", {}).get("bonus_coins", 1),
            "spin_boost": sub.get("benefits", {}).get("spin_boost", 1),
            "no_ads": sub.get("benefits", {}).get("no_ads", False),
            "expires_at": sub.get("expires_at"),
        }
