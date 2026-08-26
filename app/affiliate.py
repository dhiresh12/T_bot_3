"""Affiliate and commission system."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AffiliateProgram:
    program_id: str
    name: str
    commission_type: str  # fixed, percent, tiered
    commission_value: float
    cookie_days: int = 30
    min_payout: float = 10.0
    active: bool = True


class AffiliateService:
    def __init__(self) -> None:
        self.programs: Dict[str, AffiliateProgram] = {}
        self.referrals: Dict[str, Dict[str, Any]] = {}
        self.commissions: List[Dict[str, Any]] = []
        self._load_default_programs()

    def _load_default_programs(self) -> None:
        defaults = [
            AffiliateProgram(
                program_id="telegram_games",
                name="Telegram Games",
                commission_type="percent",
                commission_value=15.0,
                cookie_days=30,
                min_payout=5.0,
            ),
            AffiliateProgram(
                program_id="finance_app",
                name="Finance App Signup",
                commission_type="fixed",
                commission_value=5.0,
                cookie_days=7,
                min_payout=10.0,
            ),
            AffiliateProgram(
                program_id="shopping_affiliate",
                name="Shopping Affiliate",
                commission_type="percent",
                commission_value=8.0,
                cookie_days=30,
                min_payout=15.0,
            ),
        ]
        for p in defaults:
            self.programs[p.program_id] = p

    def get_programs(self) -> List[Dict[str, Any]]:
        return [
            {
                "program_id": p.program_id,
                "name": p.name,
                "commission_type": p.commission_type,
                "commission_value": p.commission_value,
                "cookie_days": p.cookie_days,
                "min_payout": p.min_payout,
                "active": p.active,
            }
            for p in self.programs.values()
        ]

    def generate_affiliate_link(self, user_id: int, program_id: str) -> str:
        program = self.programs.get(program_id)
        if not program or not program.active:
            return ""
        base = os.getenv("AFFILIATE_BASE_URL", "https://xio-payplus.onrender.com")
        return f"{base}/api/affiliate/click/{user_id}/{program_id}"

    def record_click(self, user_id: int, program_id: str, ip_hash: str = "", device_hash: str = "") -> Dict[str, Any]:
        program = self.programs.get(program_id)
        if not program or not program.active:
            return {"success": False, "reason": "invalid_program"}
        key = f"{user_id}:{program_id}:{ip_hash}"
        self.referrals[key] = {
            "user_id": user_id,
            "program_id": program_id,
            "ip_hash": ip_hash,
            "device_hash": device_hash,
            "clicked_at": self._utcnow().isoformat(),
            "converted": False,
        }
        return {"success": True, "cookie_days": program.cookie_days}

    def record_conversion(self, user_id: int, program_id: str, sale_amount: float = 0.0) -> tuple[bool, str, Dict[str, Any]]:
        program = self.programs.get(program_id)
        if not program or not program.active:
            return False, "Invalid program", {}
        if program.commission_type == "fixed":
            commission = program.commission_value
        elif program.commission_type == "percent":
            commission = round(sale_amount * (program.commission_value / 100), 2)
        else:
            commission = 0.0
        commission_entry = {
            "user_id": user_id,
            "program_id": program_id,
            "sale_amount": sale_amount,
            "commission": commission,
            "status": "pending",
            "timestamp": self._utcnow().isoformat(),
        }
        self.commissions.append(commission_entry)
        return True, f"Conversion recorded. Commission: ₹{commission:.2f}", {"commission": commission, "status": "pending"}

    def get_user_commissions(self, user_id: int) -> Dict[str, Any]:
        user_commissions = [c for c in self.commissions if c.get("user_id") == user_id]
        total_pending = sum(c["commission"] for c in user_commissions if c["status"] == "pending")
        total_paid = sum(c["commission"] for c in user_commissions if c["status"] == "paid")
        return {
            "total_pending": round(total_pending, 2),
            "total_paid": round(total_paid, 2),
            "commissions": user_commissions[-20:],
        }

    def _utcnow(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).replace(tzinfo=None)
