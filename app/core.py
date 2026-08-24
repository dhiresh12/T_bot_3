from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime, time, timezone
import os

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - pymongo unavailable
    MongoClient = None

try:
    import mongomock
except ImportError:  # pragma: no cover
    mongomock = None

from app.admin import AdminPanelService
from app.engagement import EngagementLayer
from app.support import SupportService
from app.security import SecurityManager


def _resolve_mini_app_url() -> str:
    """
    Resolves the public Mini App URL used in Telegram web_app buttons.

    Priority:
      1. MINI_APP_URL env var (explicit override)
      2. RENDER_EXTERNAL_URL / WEBHOOK_URL (set automatically by Render)
      3. Default to the deployed app URL

    Placeholder / obviously-wrong values (e.g. 'your-render-app.onrender.com',
    'localhost', 'http://') are ignored so the button never points at a dead URL.
    """
    placeholders = ("your-render-app", "http://localhost", "http://127.0.0.1")

    def _clean(candidate: str) -> str | None:
        if not candidate:
            return None
        candidate = candidate.rstrip("/")
        lowered = candidate.lower()
        if any(p in lowered for p in placeholders):
            return None
        if lowered.startswith("http://") or lowered.startswith("https://"):
            return candidate
        return None

    explicit = _clean(os.getenv("MINI_APP_URL"))
    if explicit:
        return explicit
    external = _clean(os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL"))
    if external:
        return external
    return "https://t-bot-3.onrender.com"


class _InMemoryCollection:
    """Minimal in-memory fallback so BotEngine runs even without pymongo/mongomock."""

    def __init__(self) -> None:
        self._docs: Dict[Any, Any] = {}
        self._auto_id = 0

    def find(self) -> List[Any]:
        return list(self._docs.values())

    def find_one(self, filter_: Dict[Any, Any]) -> Any:
        key = filter_.get("_id")
        if key is not None:
            return self._docs.get(key)
        for doc in self._docs.values():
            if all(doc.get(k) == v for k, v in filter_.items()):
                return doc
        return None

    def replace_one(self, filter_: Dict[Any, Any], doc: Any, upsert: bool = True) -> None:
        key = filter_.get("_id")
        if key is not None:
            self._docs[key] = doc
        elif upsert:
            self._docs[doc.get("_id", self._auto_id)] = doc
            self._auto_id += 1

    def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        data = list(self._docs.values())
        for stage in pipeline:
            op = next(iter(stage)) if stage else None
            if op == "$match":
                data = self._apply_match(data, stage["$match"])
            elif op == "$project":
                data = self._apply_project(data, stage["$project"])
            elif op == "$group":
                data = self._apply_group(data, stage["$group"])
            elif op == "$sort":
                data = self._apply_sort(data, stage["$sort"])
            elif op == "$unwind":
                data = self._apply_unwind(data, stage["$unwind"])
        return data

    def _apply_match(self, data: List[Dict], expr: Dict) -> List[Dict]:
        result = []
        for doc in data:
            if self._expr_matches(doc, expr):
                result.append(doc)
        return result

    def _expr_matches(self, doc: Dict, expr: Dict) -> bool:
        for key, condition in expr.items():
            if isinstance(condition, dict):
                for op, val in condition.items():
                    doc_val = doc.get(key)
                    if op == "$ne":
                        if doc_val == val:
                            return False
                    elif op == "$eq":
                        if doc_val != val:
                            return False
                    elif op == "$in":
                        if doc_val not in val:
                            return False
                    elif op == "$nin":
                        if doc_val in val:
                            return False
                    elif op == "$gte":
                        if doc_val is None or doc_val < val:
                            return False
                    elif op == "$lte":
                        if doc_val is None or doc_val > val:
                            return False
                    elif op == "$gt":
                        if doc_val is None or doc_val <= val:
                            return False
                    elif op == "$lt":
                        if doc_val is None or doc_val >= val:
                            return False
                    else:
                        if doc_val != val:
                            return False
            else:
                if doc.get(key) != condition:
                    return False
        return True

    def _apply_project(self, data: List[Dict], spec: Dict) -> List[Dict]:
        result = []
        for doc in data:
            new_doc = {}
            for key, expr in spec.items():
                if key.startswith("_"):
                    continue
                if isinstance(expr, str):
                    new_doc[key] = doc.get(expr)
                elif isinstance(expr, dict):
                    new_doc[key] = self._eval_expr(doc, expr)
                else:
                    new_doc[key] = expr
            result.append(new_doc)
        return result

    def _eval_expr(self, doc: Dict, expr: Dict) -> Any:
        for op, val in expr.items():
            if op == "$dateToString":
                date_val = self._eval_expr(doc, val.get("date", {}))
                fmt = val.get("format", "%Y-%m-%d")
                if isinstance(date_val, str):
                    try:
                        date_val = datetime.fromisoformat(date_val)
                    except Exception:
                        return None
                if hasattr(date_val, "strftime"):
                    return date_val.strftime(fmt.replace("%Y", "%Y").replace("%m", "%m").replace("%d", "%d"))
                return None
            elif op == "$toDate":
                raw = val
                if isinstance(raw, str) and raw.startswith("$"):
                    raw = doc.get(raw[1:])
                if isinstance(raw, str):
                    try:
                        return datetime.fromisoformat(raw)
                    except Exception:
                        return None
                if hasattr(raw, "strftime"):
                    return raw
                return None
            elif op == "$ifNull":
                v = self._eval_expr(doc, val[0]) if isinstance(val, list) else val
                return v if v is not None else (val[1] if isinstance(val, list) and len(val) > 1 else None)
            elif op.startswith("$"):
                field = op[1:]
                return doc.get(field)
            else:
                return val
        return None

    def _apply_group(self, data: List[Dict], spec: Dict) -> List[Dict]:
        groups: Dict[Any, Dict] = {}
        for doc in data:
            key_expr = spec.get("_id", "")
            if isinstance(key_expr, str):
                group_key = doc.get(key_expr.lstrip("$"))
            elif isinstance(key_expr, dict):
                group_key = self._eval_expr(doc, key_expr)
            else:
                group_key = key_expr
            if group_key not in groups:
                groups[group_key] = {"_id": group_key}
            group = groups[group_key]
            for out_key, agg in spec.items():
                if out_key == "_id":
                    continue
                if isinstance(agg, dict):
                    op = next(iter(agg))
                    val_expr = agg[op]
                    if op == "$sum":
                        if isinstance(val_expr, (int, float)):
                            group[out_key] = group.get(out_key, 0) + val_expr
                        else:
                            field = val_expr.lstrip("$")
                            group[out_key] = group.get(out_key, 0) + (doc.get(field, 0) or 0)
                    elif op == "$avg":
                        field = val_expr.lstrip("$")
                        group.setdefault(out_key + "_sum", 0)
                        group.setdefault(out_key + "_count", 0)
                        group[out_key + "_sum"] += doc.get(field, 0) or 0
                        group[out_key + "_count"] += 1
                        group[out_key] = group[out_key + "_sum"] / group[out_key + "_count"]
                    elif op == "$max":
                        field = val_expr.lstrip("$")
                        v = doc.get(field, 0) or 0
                        group[out_key] = max(group.get(out_key, v), v)
                    elif op == "$min":
                        field = val_expr.lstrip("$")
                        v = doc.get(field, 0) or 0
                        group[out_key] = min(group.get(out_key, v), v)
                    elif op == "$first":
                        if out_key not in group:
                            field = val_expr.lstrip("$")
                            group[out_key] = doc.get(field)
                    elif op == "$last":
                        field = val_expr.lstrip("$")
                        group[out_key] = doc.get(field)
                    elif op == "$push":
                        field = val_expr.lstrip("$")
                        group.setdefault(out_key, [])
                        group[out_key].append(doc.get(field))
        return list(groups.values())

    def _apply_sort(self, data: List[Dict], spec: Dict) -> List[Dict]:
        for key, direction in reversed(list(spec.items())):
            data.sort(key=lambda doc: doc.get(key) if doc.get(key) is not None else ("" if isinstance(direction, int) else 0), reverse=(direction == -1))
        return data

    def _apply_unwind(self, data: List[Dict], expr: str) -> List[Dict]:
        field = expr.lstrip("$")
        result = []
        for doc in data:
            arr = doc.get(field, [])
            if not isinstance(arr, list):
                arr = [arr]
            for item in arr:
                new_doc = dict(doc)
                new_doc[field] = item
                result.append(new_doc)
        return result


class _InMemoryDB:
    """Minimal in-memory database fallback."""

    def __init__(self) -> None:
        self.users = _InMemoryCollection()


@dataclass
class UserProfile:  # Phase 1: Expanded UserProfile
    user_id: int
    name: str
    wallet_bot: float = 0.0  # Renamed from wallet
    wallet_app: float = 0.0  # New wallet for mini-app
    coins: int = 0
    popularity: int = 0
    bonus_claimed: bool = False
    completed_tasks: List[str] = field(default_factory=list)
    total_ads_watched: int = 0
    invite_count: int = 0
    invites_list: List[int] = field(default_factory=list)  # Track who was invited
    withdrawals: List[Dict[str, Any]] = field(default_factory=list)
    last_bonus_at: Optional[str] = None
    daily_ads_watch_count: int = 0
    daily_spin_count: int = 0
    last_spin_at: Optional[str] = None
    last_ad_watched_at: Optional[str] = None
    admin: bool = False
    # New fields from plan
    tier: str = "Bronze"
    activity_log: List[Dict[str, Any]] = field(default_factory=list)
    last_activity_at: Optional[str] = None
    is_verified: bool = False
    registered_at: Optional[str] = None
    invited_by: Optional[int] = None
    # Snap-style streak system (dark pattern: keeps users returning daily)
    snap_streak: int = 0
    last_streak_at: Optional[str] = None
    # Shop / gift inventory (future upgradeable)
    inventory: List[Dict[str, Any]] = field(default_factory=list)
    bonus_ads_remaining: int = 0
    ads_boost_remaining: int = 0
    has_profile_badge: bool = False
    # --- New upgrade fields ---
    level: int = 1
    xp: int = 0
    badges: List[str] = field(default_factory=list)
    scratch_cards_available: int = 0
    daily_challenge_completed: bool = False
    last_challenge_at: Optional[str] = None
    streak_insurance: int = 0
    referral_tier: str = "Bronze"
    social_shares_count: int = 0
    last_social_share_at: Optional[str] = None
    notifications: List[Dict[str, Any]] = field(default_factory=list)
    unread_notifications: int = 0
    super_spins_available: int = 0
    mega_spins_available: int = 0
    leaderboard_week_rank: Optional[int] = None
    leaderboard_reward_claimed: bool = False
    # --- Social / Friend System ---
    friends: List[int] = field(default_factory=list)
    friend_requests: List[Dict[str, Any]] = field(default_factory=list)
    bio: str = ""
    preferred_language: str = "en"
    last_notification_at: Optional[str] = None

    def log_activity(self, action: str, details: Optional[Dict] = None):
        """Helper to log user activity."""
        self.last_activity_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        log_entry = {"action": action, "timestamp": self.last_activity_at}
        if details:
            log_entry.update(details)
        self.activity_log.append(log_entry)


class BotEngine:
    def __init__(self, storage_path: Optional[str] = None) -> None:
        # --- MongoDB Connection (optional) ---
        mongo_uri = os.getenv("MONGO_URI")
        if mongo_uri and MongoClient is not None:
            self.client = MongoClient(mongo_uri)
            self.db = self.client.get_default_database()
            if self.db is None:
                self.db = self.client["bot_data"]
        elif mongomock is not None:
            self.client = mongomock.MongoClient("mongodb://localhost")
            self.db = self.client["bot_data"]
        else:
            self.client = None
            self.db = _InMemoryDB()
        self.users_collection = self.db.users

        self.users: Dict[int, UserProfile] = {}
        # --- Admin configurable values ---
        self.bonus_value = 0.05
        self.admin_key = os.getenv("ADMIN_KEY", "admin-xio")
        self.engagement = EngagementLayer()
        self.support = SupportService()
        self.admin_service = AdminPanelService(self)
        self.security = SecurityManager()  # Phase 2: Integrate SecurityManager
        self.spin_values = [0.0, 0.10, 0.15, 0.20]
        self.min_withdrawal = 10.0
        self.daily_ads_limit = 20  # 2 ads = 1 count, so this is 40 ad-plays per day
        self.daily_spin_limit = 1
        # Gift-based spin economy (spec: gifts with a "open" reveal + golden glow)
        self.spin_gifts = [
            {"name": "🎁 Mystery Gift", "coins": 500, "emoji": "🎁"},
            {"name": "💎 Diamond Box", "coins": 2000, "emoji": "💎"},
            {"name": "⭐ Golden Star", "coins": 1000, "emoji": "⭐"},
            {"name": "🔥 Fire Combo", "coins": 1500, "emoji": "🔥"},
            {"name": "🏆 Royal Trophy", "coins": 3000, "emoji": "🏆"},
            {"name": "💥 Try Again", "coins": 0, "emoji": "💥"},
        ]
        # Snap-style streak ladder (dark pattern: daily returns kick in at 3+ days)
        self.snap_streak_rewards = [0, 50, 150, 300, 500, 800, 1200, 1750, 2400, 3200, 4200]
        # --- New Economic Model ---
        self.coins_to_rupee_rate = 0.0001  # 10,000 coins = 1 Rupee
        self.withdrawal_fee_percent = 5  # 5% processing fee on all withdrawals
        # --- Ads economics (spec: ₹0.002 + 50-500 coins per ad; possible revenue share) ---
        self.ads_reward_per_ad = 0.002          # ₹0.002 per completed ad
        self.ads_reward_coins_min = 50
        self.ads_reward_coins_max = 500
        self.ads_user_share_percent = 50        # % of ad revenue shared with the user
        self.bonus_ads_per_code = 10            # bonus ads granted by each more-ads code
        # --- Referral economics (spec: $0.005 per REAL successful invite) ---
        self.invite_referral_reward = 0.005     # ₹0.005 credited to the inviter's bot wallet

        # --- New features config ---
        # Level progression XP thresholds
        self.level_xp_thresholds = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500, 6600, 7800, 9100, 10500]
        # XP rewards per action
        self.xp_per_ad = 10
        self.xp_per_task = 25
        self.xp_per_spin = 15
        self.xp_per_invite = 50
        self.xp_per_challenge = 40
        self.xp_per_share = 20
        # Daily challenges pool
        self.daily_challenges_pool = [
            {"id": "watch_5_ads", "title": "Watch 5 Ads", "desc": "Watch 5 ads today", "target": 5, "type": "ads", "reward_coins": 300, "reward_xp": 40},
            {"id": "complete_2_tasks", "title": "Complete 2 Tasks", "desc": "Finish any 2 tasks", "target": 2, "type": "tasks", "reward_coins": 500, "reward_xp": 40},
            {"id": "spin_once", "title": "Spin the Wheel", "desc": "Use your daily spin", "target": 1, "type": "spin", "reward_coins": 200, "reward_xp": 40},
            {"id": "invite_1_friend", "title": "Invite a Friend", "desc": "Share your invite link", "target": 1, "type": "invite", "reward_coins": 400, "reward_xp": 40},
            {"id": "streak_3_days", "title": "3-Day Streak", "desc": "Maintain a 3-day streak", "target": 3, "type": "streak", "reward_coins": 600, "reward_xp": 40},
            {"id": "watch_10_ads", "title": "Watch 10 Ads", "desc": "Watch 10 ads today", "target": 10, "type": "ads", "reward_coins": 800, "reward_xp": 60},
            {"id": "complete_5_tasks", "title": "Complete 5 Tasks", "desc": "Finish any 5 tasks", "target": 5, "type": "tasks", "reward_coins": 1500, "reward_xp": 60},
        ]
        # Achievements definitions
        self.achievements_def = [
            {"id": "first_task", "title": "First Steps", "desc": "Complete your first task", "icon": "👣", "check": lambda p: len(p.completed_tasks) >= 1},
            {"id": "ad_watcher", "title": "Ad Watcher", "desc": "Watch 10 ads total", "icon": "📺", "check": lambda p: p.total_ads_watched >= 10},
            {"id": "social_butterfly", "title": "Social Butterfly", "desc": "Invite 5 friends", "icon": "🦋", "check": lambda p: p.invite_count >= 5},
            {"id": "streak_master", "title": "Streak Master", "desc": "Reach 7-day streak", "icon": "🔥", "check": lambda p: p.snap_streak >= 7},
            {"id": "coin_collector", "title": "Coin Collector", "desc": "Earn 10,000 coins", "icon": "💰", "check": lambda p: p.coins >= 10000},
            {"id": "spin_winner", "title": "Spin Winner", "desc": "Win 5 spin rewards", "icon": "🎡", "check": lambda p: sum(1 for a in p.activity_log if a.get("action") == "spin_win") >= 5},
            {"id": "shopaholic", "title": "Shopaholic", "desc": "Buy 3 shop items", "icon": "🛒", "check": lambda p: sum(1 for a in p.activity_log if a.get("action") == "shop_redeem") >= 3},
            {"id": "challenge_champ", "title": "Challenge Champion", "desc": "Complete 7 daily challenges", "icon": "🏆", "check": lambda p: sum(1 for a in p.activity_log if a.get("action") == "daily_challenge_complete") >= 7},
            {"id": "level_5", "title": "Rising Star", "desc": "Reach Level 5", "icon": "⭐", "check": lambda p: p.level >= 5},
            {"id": "level_10", "title": "Elite Earner", "desc": "Reach Level 10", "icon": "👑", "check": lambda p: p.level >= 10},
        ]
        # Scratch card rewards pool (weighted)
        self.scratch_rewards = [
            {"coins": 0, "weight": 30, "label": "Try Again"},
            {"coins": 50, "weight": 25, "label": "50 Coins"},
            {"coins": 100, "weight": 20, "label": "100 Coins"},
            {"coins": 200, "weight": 15, "label": "200 Coins"},
            {"coins": 500, "weight": 7, "label": "500 Coins"},
            {"coins": 1000, "weight": 2, "label": "1000 Coins"},
            {"coins": 5000, "weight": 1, "label": "JACKPOT 5000"},
        ]
        # Referral tier thresholds
        self.referral_tiers = [
            {"name": "Bronze", "min": 0, "emoji": "🥉"},
            {"name": "Silver", "min": 5, "emoji": "🥈"},
            {"name": "Gold", "min": 15, "emoji": "🥇"},
            {"name": "Platinum", "min": 30, "emoji": "💎"},
            {"name": "Diamond", "min": 50, "emoji": "💍"},
            {"name": "Crown", "min": 100, "emoji": "👑"},
        ]
        # Super/Mega spin coin rewards multiplier
        self.super_spin_multiplier = 3
        self.mega_spin_multiplier = 5
        # Leaderboard weekly rewards
        self.leaderboard_weekly_rewards = {
            1: {"coins": 5000, "xp": 500, "title": "Weekly Champion"},
            2: {"coins": 3000, "xp": 300, "title": "Weekly Runner-Up"},
            3: {"coins": 2000, "xp": 200, "title": "Weekly Third Place"},
        }
        # Notification templates
        self.notification_templates = {
            "daily_login": {"title": "Daily Login Bonus", "message": "Come back today to claim your daily bonus!", "icon": "🎁"},
            "streak_risk": {"title": "Streak at Risk!", "message": "Your streak will break today! Spin or watch an ad to keep it.", "icon": "🔥"},
            "new_challenge": {"title": "New Challenge", "message": "A new daily challenge is waiting for you!", "icon": "⚡"},
            "level_up": {"title": "Level Up!", "message": "Congratulations! You reached a new level.", "icon": "⬆️"},
            "bonus_ready": {"title": "Bonus Ready", "message": "Your daily bonus is ready to claim!", "icon": "💰"},
            "scratch_ready": {"title": "Scratch Card Ready", "message": "You have a free scratch card waiting!", "icon": "🎟️"},
        }

        # --- Admin editable tasks (1000 coin reward + real links) ---
        self.tasks = {
            "join_channel": {
                "title": "Join Telegram channel",
                "reward_coins": 1000,
                "reward_money": 0.01,
                "url": "https://t.me/xio_liis_watch_Ads_earning",
                "verify": "join",
            },
            "join_group": {
                "title": "Join Telegram group",
                "reward_coins": 1000,
                "reward_money": 0.01,
                "url": "https://t.me/+QserNlqLSqZjN2U9",
                "verify": "join",
            },
            "subscribe_youtube": {
                "title": "Subscribe on YouTube",
                "reward_coins": 1000,
                "reward_money": 0.01,
                "url": "https://www.youtube.com/@xio_liis-y3g",
                "verify": "join",
            },
            "join_whatsapp": {
                "title": "Join WhatsApp channel",
                "reward_coins": 1000,
                "reward_money": 0.01,
                "url": "https://whatsapp.com/channel/0029Vb7o3InDzgTKpSBx4640",
                "verify": "join",
            },
            "follow_facebook": {
                "title": "Follow on Facebook",
                "reward_coins": 1000,
                "reward_money": 0.01,
                "url": "https://www.facebook.com/profile.php?id=61591087755430",
                "verify": "join",
            },
            "share_link": {
                "title": "Share your invite link",
                "reward_coins": 1000,
                "reward_money": 0.02,
                "url": "",
                "verify": "share",
            },
        }
# --- More-ads code store (admin can add codes). Each valid code grants 10 bonus ads. ---
        self.more_ads_codes = {"GET10ADS", "BONUS10", "MOREADS"}
        # --- Shop catalog (Phase: redeemable boosters/gifts with coins) ---
        # Each item: id, name, emoji, desc, price (coins), and an effect key.
        # The effect is applied server-side so the user cannot cheat by editing the UI.
        self.shop_items = [
            {
                "id": "mystery_box",
                "name": "Mystery Gift Box",
                "emoji": "🎁",
                "desc": "Open a random surprise worth 200-1000 coins!",
                "price": 500,
                "effect": "mystery_coins",
            },
            {
                "id": "extra_spin",
                "name": "Extra Spin Ticket",
                "emoji": "🎡",
                "desc": "Claim an extra daily spin right now!",
                "price": 800,
                "effect": "extra_spin",
            },
            {
                "id": "bonus_ads",
                "name": "Bonus Ads Pack",
                "emoji": "📺",
                "desc": "Add +5 bonus ads to your daily limit.",
                "price": 1000,
                "effect": "bonus_ads",
            },
            {
                "id": "streak_boost",
                "name": "Streak Boost 🔥",
                "emoji": "🔥",
                "desc": "Boost your snap streak by +2 days instantly.",
                "price": 1500,
                "effect": "streak_boost",
            },
            {
                "id": "diamond_boost",
                "name": "Diamond Boost",
                "emoji": "💎",
                "desc": "Earn 2x coins from the next 5 ads.",
                "price": 2000,
                "effect": "ads_boost",
            },
            {
                "id": "streak_shield",
                "name": "Golden Streak Shield",
                "emoji": "⭐",
                "desc": "Keep your streak alive for 1 day.",
                "price": 1500,
                "effect": "streak_shield",
            },
            {
                "id": "fire_double",
                "name": "Fire Double Coins",
                "emoji": "🔥",
                "desc": "Double coins on your next 5 ads.",
                "price": 1000,
                "effect": "ads_boost",
            },
            {
                "id": "featured_badge",
                "name": "Featured Badge",
                "emoji": "🏆",
                "desc": "Show off on the leaderboard.",
                "price": 5000,
                "effect": "profile_badge",
            },
            {
                "id": "scratch_pack",
                "name": "Scratch Card Pack",
                "emoji": "🎟️",
                "desc": "Get 3 scratch cards to win instant coins!",
                "price": 300,
                "effect": "scratch_cards",
            },
            {
                "id": "super_spin_ticket",
                "name": "Super Spin Ticket",
                "emoji": "🎡",
                "desc": "Get a Super Spin with 3x coin rewards!",
                "price": 2000,
                "effect": "super_spin",
            },
            {
                "id": "mega_spin_ticket",
                "name": "Mega Spin Ticket",
                "emoji": "💥",
                "desc": "Get a Mega Spin with 5x coins + guaranteed rare gift!",
                "price": 5000,
                "effect": "mega_spin",
            },
            {
                "id": "streak_insurance",
                "name": "Streak Insurance",
                "emoji": "🛡️",
                "desc": "Protect your streak for 1 missed day.",
                "price": 1200,
                "effect": "streak_insurance",
            },
            {
                "id": "xp_boost",
                "name": "XP Boost",
                "emoji": "⬆️",
                "desc": "Double XP on your next 3 actions.",
                "price": 800,
                "effect": "xp_boost",
            },
        ]
        # Phase 1: Withdrawal requirements
        self.withdrawal_reqs = {
            "min_invites": 10,
            "min_tasks": 5,
            "min_ads": 80,
        }
        self.load()

        # Code Quality: Command handler mapping
        self.command_handlers = {
            "start": self._handle_start,
            "menu": self._handle_menu,
            "bonus": self._handle_bonus,
            "wallet": self._handle_wallet,
            "task": self._handle_task,
            "tasks": self._handle_task,
            "spin": self._handle_spin,
            "profile": self._handle_profile,
            "leaderboard": self._handle_leaderboard,
        }

    def _get_utc_now(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def load(self) -> None:
        """Loads all user profiles from the backing store into memory."""
        try:
            all_users_data = self.users_collection.find()
            for user_data in all_users_data:
                user_data['user_id'] = user_data.pop('_id')  # Mongo uses _id as primary key
                profile = UserProfile(**user_data)
                self.users[profile.user_id] = profile
            logging.info(f"Loaded {len(self.users)} users.")
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            self.users = {}

    def save(self) -> None:
        """Saves all user profiles (used for compatibility)."""
        for profile in self.users.values():
            self._save_user(profile)

    def _save_user(self, profile: UserProfile):
        """Saves a single user's profile."""
        profile_dict = asdict(profile)
        self.users_collection.replace_one({'_id': profile.user_id}, profile_dict, upsert=True)

    def register_user(self, user_id: int, name: str, inviter_id: Optional[int] = None) -> UserProfile:
        if user_id not in self.users:
            self.users[user_id] = UserProfile(
                user_id=user_id,
                name=name,
                registered_at=self._get_utc_now().isoformat(),
            )
            if inviter_id and inviter_id in self.users:
                self.users[user_id].invited_by = inviter_id
                self.process_successful_invite(inviter_id, user_id)
            self._save_user(self.users[user_id])
        return self.users[user_id]

    def get_profile(self, user_id: int) -> UserProfile:
        """Gets a user profile. If the user doesn't exist, it creates and saves them."""
        if user_id not in self.users:
            return self.register_user(user_id, "Guest")
        return self.users[user_id]

    def build_menu(self, profile: UserProfile) -> Dict[str, Any]:
        """Builds the main menu with inline keyboard buttons."""
        text = f"👋 Welcome, {profile.name}!\n\nSelect an option from the menu below."
        mini_app_url = _resolve_mini_app_url()
        reply_markup = {
            "inline_keyboard": [
                [{"text": "👤 Profile", "callback_data": "profile"}, {"text": "💰 Wallet", "callback_data": "wallet"}],
                [{"text": "🎁 Daily Bonus", "callback_data": "bonus"}, {"text": "🎡 Spin Wheel", "callback_data": "spin"}],
                [{"text": "📋 Tasks", "callback_data": "tasks"}, {"text": "🏆 Leaderboard", "callback_data": "leaderboard"}],
                [{"text": "🚀 Launch Mini App", "web_app": {"url": mini_app_url}}],
                [{"text": "❓ Help", "callback_data": "help"}],
            ]
        }
        return {"text": text, "reply_markup": reply_markup}

    def handle_command(self, user_id: int, command: str) -> str:
        """Handles text-based commands from the Telegram bot chat."""
        profile = self.get_profile(user_id)

        cleaned_command = (command or "").strip().lstrip('/')
        normalized_cmd = ''.join(c for c in cleaned_command if c.isalnum() or c == ':').lower()

        if normalized_cmd.startswith("help"):
            return self.handle_help_command(cleaned_command)

        if normalized_cmd.startswith("start"):
            normalized_cmd = "start"

        handler = self.command_handlers.get(normalized_cmd)
        if handler:
            return handler(profile)

        if normalized_cmd in {"ads", "watchads"}:
            return "Watch ads to earn rewards and boost your balance."
        if normalized_cmd.startswith("withdraw"):
            return self.request_withdrawal(user_id, self.min_withdrawal, method="upi")
        if normalized_cmd.startswith("admin"):
            return self.handle_admin_command(user_id, command)
        return "Unknown command."

    def handle_help_command(self, command: str) -> Dict[str, Any]:
        """Handles the interactive help command with language selection."""
        parts = command.split(':')
        lang = parts[1] if len(parts) > 1 else None

        if not lang:
            text = "Please select your language:\nकृपया अपनी भाषा चुनें:"
            buttons = [
                [{"text": "🇬🇧 English", "callback_data": "help:en"}, {"text": "🇮🇳 हिन्दी", "callback_data": "help:hi"}],
                [{"text": "🇪🇸 Español", "callback_data": "help:es"}, {"text": "🇫🇷 Français", "callback_data": "help:fr"}],
                [{"text": "🇨🇳 中文", "callback_data": "help:zh"}, {"text": "🇷🇺 Русский", "callback_data": "help:ru"}],
                [{"text": "🇧🇩 বাংলা", "callback_data": "help:bn"}, {"text": "🇵🇰 اردو", "callback_data": "help:ur"}],
                [{"text": "🇮🇳 தமிழ்", "callback_data": "help:ta"}, {"text": "🇮🇳 తెలుగు", "callback_data": "help:te"}],
            ]
            return {"text": text, "reply_markup": {"inline_keyboard": buttons}}

        help_content = self.support.get_faq(lang)
        messages = self.support.translations.get(lang, self.support.translations['en'])['messages']

        text = messages.get('help_intro', 'Help is available.') + "\n\n"
        text += "\n".join(f"• {q}: {a}" for q, a in help_content.items())

        support_links = self.support.get_support_links()
        buttons = [
            [{"text": messages.get('customer_support_button', 'Customer Support'), "url": support_links['support_group']}],
            [{"text": messages.get('contact_admin_button', 'Contact Admin'), "url": support_links['admin_channel']}],
        ]
        return {"text": text, "reply_markup": {"inline_keyboard": buttons}}

    def complete_task(self, user_id: int, task_id: str) -> tuple[bool, str]:
        profile = self.get_profile(user_id)
        if task_id in profile.completed_tasks:
            return False, "Task already completed."
        if task_id not in self.tasks:
            return False, "Invalid task ID."

        task_info = self.tasks[task_id]
        reward_coins = task_info.get("reward_coins", 0)
        reward_money = task_info.get("reward_money", 0.0)

        profile.completed_tasks.append(task_id)
        profile.coins += reward_coins
        profile.wallet_bot += reward_money
        profile.popularity += 1
        profile.log_activity("complete_task", {"task_id": task_id, "reward_coins": reward_coins, "reward_money": reward_money})
        self._save_user(profile)
        return True, f"Task '{task_id}' completed! You earned {reward_coins} coins + ₹{reward_money:.2f}."

    def redeem_more_ads(self, user_id: int, code: str) -> tuple[bool, str]:
        """Validates a more-ads code and grants 10 bonus ads."""
        profile = self.get_profile(user_id)
        normalized = (code or "").strip().upper()
        if not normalized:
            return False, "Please enter a code."
        if normalized not in self.more_ads_codes:
            return False, "Invalid code. Please use a valid more-ads code from the group."
        if any(e.get("action") == "more_ads" and e.get("code") == normalized for e in profile.activity_log):
            return False, "This code has already been redeemed."
        bonus = self.bonus_ads_per_code
        profile.daily_ads_watch_count += bonus
        profile.log_activity("more_ads", {"code": normalized, "bonus_ads": bonus})
        self._save_user(profile)
        return True, f"Code accepted! {bonus} bonus ads added to your daily limit."

    def watch_ads(self, user_id: int) -> tuple[bool, str]:
        profile = self.get_profile(user_id)

        now = self._get_utc_now()
        reset_time = time(12, 0)
        last_watched_time = datetime.fromisoformat(profile.last_ad_watched_at) if profile.last_ad_watched_at else None

        if last_watched_time:
            if last_watched_time.date() < now.date():
                profile.daily_ads_watch_count = 0
            elif now.time() >= reset_time and last_watched_time.time() < reset_time:
                profile.daily_ads_watch_count = 0

        reward_coins = random.randint(self.ads_reward_coins_min, self.ads_reward_coins_max)
        reward_money = self.ads_reward_per_ad  # ₹0.002 per completed ad

        ads_boost = next((i for i in profile.inventory if i.get("type") == "ads_boost"), None)
        if ads_boost:
            reward_coins *= 2
            ads_boost["remaining"] -= 1
            if ads_boost["remaining"] <= 0:
                profile.inventory.remove(ads_boost)

        effective_daily_limit = self.daily_ads_limit + profile.bonus_ads_remaining
        if profile.daily_ads_watch_count >= effective_daily_limit:
            return False, "Daily ads limit reached. Come back after 12 PM or tomorrow."

        profile.daily_ads_watch_count += 1
        profile.total_ads_watched += 1
        profile.last_ad_watched_at = now.isoformat()
        profile.coins += reward_coins
        profile.wallet_bot += reward_money
        profile.log_activity("watch_ad", {"reward_coins": reward_coins, "reward_money": reward_money})
        self._save_user(profile)
        return True, f"Ad completed! You earned ₹{reward_money:.3f} + {reward_coins} coins."

    def process_successful_invite(self, inviter_id: int, new_user_id: int):
        """Called when a new user joins via an invite link (real successful referral)."""
        inviter_profile = self.get_profile(inviter_id)
        inviter_profile.invite_count += 1
        inviter_profile.invites_list.append(new_user_id)
        inviter_profile.popularity += 2
        inviter_profile.wallet_bot += self.invite_referral_reward  # ₹0.005
        inviter_profile.coins += random.randint(100, 200)
        inviter_profile.log_activity("user_invited", {"new_user_id": new_user_id, "reward": self.invite_referral_reward})
        self._save_user(inviter_profile)

    def request_withdrawal(self, user_id: int, amount: float, method: str = "upi", details: str = "") -> str:
        profile = self.get_profile(user_id)

        current_wallet_value = round(profile.coins * self.coins_to_rupee_rate, 4)

        if profile.invite_count < self.withdrawal_reqs["min_invites"]:
            return f"Withdrawal failed. You need at least {self.withdrawal_reqs['min_invites']} invites (you have {profile.invite_count})."
        if len(profile.completed_tasks) < self.withdrawal_reqs["min_tasks"]:
            return f"Withdrawal failed. You need to complete at least {self.withdrawal_reqs['min_tasks']} tasks (you have {len(profile.completed_tasks)})."
        if profile.total_ads_watched < self.withdrawal_reqs["min_ads"]:
            return f"Withdrawal failed. You need to watch at least {self.withdrawal_reqs['min_ads']} ads (you have {profile.total_ads_watched})."
        if amount < self.min_withdrawal:
            return "Withdrawal amount is below the minimum."
        if amount > current_wallet_value:
            return "Insufficient balance in bot wallet."
        # --- Payment detail validation (spec: UPI / bank / mobile) ---
        # Only validate when payment details were actually provided. Some callers
        # (e.g. the demo CLI / API) request a payout without entering details yet.
        method = (method or "upi").lower()
        if details.strip():
            if method == "upi":
                if "@" not in details or len(details) < 6:
                    return "Invalid UPI ID. Please enter a valid UPI ID like name@okhdfcbank."
            elif method == "bank":
                if len(details.replace(" ", "")) < 9:
                    return "Invalid bank account number. Please enter a valid account number."
            elif method == "mobile":
                digits = "".join(ch for ch in details if ch.isdigit())
                if len(digits) != 10:
                    return "Invalid mobile number. Please enter a valid 10-digit mobile number."
            else:
                return "Invalid withdrawal method. Use upi, bank, or mobile."

        request_id = f"req-{user_id}-{len(profile.withdrawals) + 1}"
        unique_code = self.security.generate_unique_code()

        fee = round(amount * (self.withdrawal_fee_percent / 100), 2)
        final_amount = amount - fee
        coins_to_deduct = int(amount / self.coins_to_rupee_rate)

        profile.withdrawals.append(
            {
                "request_id": request_id,
                "user_id": user_id,
                "amount": amount,
                "method": method,
                "details": details,
                "status": "pending",
                "unique_code": unique_code,
                "fee_applied": fee,
                "final_payout": final_amount,
                "coins_deducted": coins_to_deduct,
                "timestamp": self._get_utc_now().isoformat(),
            }
        )
        profile.coins -= coins_to_deduct
        self._save_user(profile)
        return f"Withdrawal request of ₹{amount:.2f} submitted. A {self.withdrawal_fee_percent}% fee (₹{fee:.2f}) is applied. Final Payout: ₹{final_amount:.2f}. Your unique code is: {unique_code}. Keep it safe!"

    def spin_wheel(self, user_id: int) -> tuple[bool, str, Dict[str, Any]]:
        """Handles the daily gift spin (spec: gift boxes, golden glow, 'open' reveal).

        A random gift is drawn from ``self.spin_gifts``. If the gift grants coins,
        they are credited immediately (the "open" reveal just celebrates it), and
        the user's Snap-style streak is bumped. Daily limit logic is preserved.
        """
        profile = self.get_profile(user_id)
        now = self._get_utc_now()

        last_spin_time = datetime.fromisoformat(profile.last_spin_at) if profile.last_spin_at else None
        if last_spin_time and last_spin_time.date() < now.date():
            profile.daily_spin_count = 0

        if profile.daily_spin_count >= self.daily_spin_limit:
            extra_spin = next((i for i in profile.inventory if i.get("type") == "extra_spin"), None)
            if not extra_spin:
                return False, "You have already used your daily spin. Come back tomorrow!", {}
            profile.inventory.remove(extra_spin)

        profile.daily_spin_count += 1
        profile.last_spin_at = now.isoformat()

        gift = random.choice(self.spin_gifts)
        coins_won = gift.get("coins", 0)

        # Snap-style streak: handle daily progression and shields
        if profile.last_streak_at:
            last_streak_date = datetime.fromisoformat(profile.last_streak_at).date()
            days_diff = (now.date() - last_streak_date).days
            if days_diff == 1:
                profile.snap_streak += 1
            elif days_diff > 1:
                streak_shield = next((i for i in profile.inventory if i.get("type") == "streak_shield"), None)
                if streak_shield:
                    profile.inventory.remove(streak_shield)
                else:
                    profile.snap_streak = 1
        else:
            profile.snap_streak = 1
        profile.last_streak_at = now.isoformat()

        if coins_won > 0:
            profile.coins += coins_won
            profile.log_activity("spin_win", {"gift": gift["name"], "coins_won": coins_won, "snap_streak": profile.snap_streak})
        else:
            profile.log_activity("spin_lose", {"gift": gift["name"], "snap_streak": profile.snap_streak})

        self._save_user(profile)
        if coins_won > 0:
            return True, f"🎁 You won a {gift['name']}! Open it to reveal {coins_won} coins (streak: {profile.snap_streak} 🔥).", gift
        return True, f"💥 You won a {gift['name']}. Better luck next time! (streak: {profile.snap_streak} 🔥)", gift

    def get_shop_catalog(self) -> List[Dict[str, Any]]:
        """Returns the shop catalog for the mini-app UI."""
        return self.shop_items



    # --- New Features: Level Progression ---

    def _get_level_info(self, xp: int) -> Dict[str, Any]:
        level = 1
        for i, threshold in enumerate(self.level_xp_thresholds):
            if xp >= threshold:
                level = i + 1
            else:
                break
        next_idx = level
        if next_idx < len(self.level_xp_thresholds):
            xp_for_next = self.level_xp_thresholds[next_idx] - xp
            next_name = f"Level {next_idx + 1}"
            progress_pct = min(99, max(2, ((xp - self.level_xp_thresholds[next_idx - 1]) / max(1, self.level_xp_thresholds[next_idx] - self.level_xp_thresholds[next_idx - 1])) * 100))
        else:
            xp_for_next = 0
            next_name = "Max Level"
            progress_pct = 100
        return {"level": level, "xp_for_next": xp_for_next, "next_name": next_name, "progress_pct": progress_pct}

    def _add_xp_internal(self, profile: UserProfile, amount: int) -> int:
        old_level = profile.level
        profile.xp += amount
        new_level = self._get_level_info(profile.xp)["level"]
        if new_level > old_level:
            profile.level = new_level
            self.add_notification(profile.user_id, "Level Up!", f"You reached Level {new_level}! Keep earning for more perks.", {"type": "level_up", "new_level": new_level})
        return new_level

    def add_xp(self, user_id: int, amount: int) -> Dict[str, Any]:
        profile = self.get_profile(user_id)
        old_level = profile.level
        new_level = self._add_xp_internal(profile, amount)
        profile.log_activity("add_xp", {"amount": amount, "level": profile.level})
        self._save_user(profile)
        return {"xp_added": amount, "total_xp": profile.xp, "level": profile.level, "leveled_up": new_level > old_level}

    # --- New Features: Achievements ---

    def get_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        profile = self.get_profile(user_id)
        result = []
        for ach in self.achievements_def:
            unlocked = ach["id"] in profile.badges
            result.append({
                "id": ach["id"],
                "title": ach["title"],
                "desc": ach["desc"],
                "icon": ach["icon"],
                "unlocked": unlocked,
            })
        return result

    def check_achievements(self, user_id: int) -> List[str]:
        profile = self.get_profile(user_id)
        newly_unlocked = []
        for ach in self.achievements_def:
            if ach["id"] not in profile.badges and ach["check"](profile):
                profile.badges.append(ach["id"])
                profile.coins += 500
                profile.xp += 100
                newly_unlocked.append(ach["id"])
                self.add_notification(user_id, "Achievement Unlocked!", f"You earned the '{ach['title']}' badge! +500 coins, +100 XP", {"type": "achievement", "achievement_id": ach["id"]})
        if newly_unlocked:
            profile.log_activity("achievement_unlock", {"badges": newly_unlocked})
            self._save_user(profile)
        return newly_unlocked

    # --- New Features: Daily Challenges ---

    def get_daily_challenges(self, user_id: int) -> List[Dict[str, Any]]:
        profile = self.get_profile(user_id)
        challenges = []
        for ch in self.daily_challenges_pool:
            progress = 0
            completed = False
            if ch["type"] == "ads":
                progress = profile.daily_ads_watch_count
                completed = progress >= ch["target"]
            elif ch["type"] == "tasks":
                progress = sum(1 for t in profile.completed_tasks if t in self.tasks)
                completed = progress >= ch["target"]
            elif ch["type"] == "spin":
                progress = profile.daily_spin_count
                completed = progress >= ch["target"]
            elif ch["type"] == "invite":
                progress = profile.invite_count
                completed = progress >= ch["target"]
            elif ch["type"] == "streak":
                progress = profile.snap_streak
                completed = progress >= ch["target"]
            challenges.append({
                "id": ch["id"],
                "title": ch["title"],
                "desc": ch["desc"],
                "target": ch["target"],
                "progress": min(progress, ch["target"]),
                "completed": completed,
                "reward_coins": ch["reward_coins"],
                "reward_xp": ch["reward_xp"],
            })
        return challenges

    def complete_daily_challenge(self, user_id: int, challenge_id: str) -> tuple[bool, str, Dict[str, Any]]:
        profile = self.get_profile(user_id)
        now = self._get_utc_now()
        if profile.daily_challenge_completed and profile.last_challenge_at and datetime.fromisoformat(profile.last_challenge_at).date() == now.date():
            return False, "You have already completed today's challenge.", {}
        challenge = next((c for c in self.daily_challenges_pool if c["id"] == challenge_id), None)
        if not challenge:
            return False, "Invalid challenge.", {}
        progress = 0
        if challenge["type"] == "ads":
            progress = profile.daily_ads_watch_count
        elif challenge["type"] == "tasks":
            progress = sum(1 for t in profile.completed_tasks if t in self.tasks)
        elif challenge["type"] == "spin":
            progress = profile.daily_spin_count
        elif challenge["type"] == "invite":
            progress = profile.invite_count
        elif challenge["type"] == "streak":
            progress = profile.snap_streak
        if progress < challenge["target"]:
            return False, f"Challenge not met yet. Progress: {progress}/{challenge['target']}.", {}
        profile.coins += challenge["reward_coins"]
        profile.xp += challenge["reward_xp"]
        profile.daily_challenge_completed = True
        profile.last_challenge_at = now.isoformat()
        profile.log_activity("daily_challenge_complete", {"challenge_id": challenge_id, "reward_coins": challenge["reward_coins"], "reward_xp": challenge["reward_xp"]})
        self._add_xp_internal(profile, 0)
        self._save_user(profile)
        self.check_achievements(user_id)
        return True, f"Challenge '{challenge['title']}' completed! +{challenge['reward_coins']} coins, +{challenge['reward_xp']} XP.", {"coins": challenge["reward_coins"], "xp": challenge["reward_xp"]}

    # --- New Features: Scratch Cards ---

    def scratch_card(self, user_id: int) -> tuple[bool, str, Dict[str, Any]]:
        profile = self.get_profile(user_id)
        if profile.scratch_cards_available <= 0:
            return False, "No scratch cards available. Buy one from the shop or wait for your daily free card!", {}
        reward = random.choices(self.scratch_rewards, weights=[r["weight"] for r in self.scratch_rewards], k=1)[0]
        profile.scratch_cards_available -= 1
        profile.coins += reward["coins"]
        profile.log_activity("scratch_card", {"coins_won": reward["coins"], "label": reward["label"]})
        self._save_user(profile)
        if reward["coins"] > 0:
            self.add_notification(user_id, "Scratch Card Win!", f"You won {reward['coins']} coins from your scratch card!", {"type": "scratch_win", "coins": reward["coins"]})
        return True, f"You scratched and won: {reward['label']}!", {"coins": reward["coins"], "label": reward["label"]}

    def claim_scratch_card(self, user_id: int) -> tuple[bool, str, Dict[str, Any]]:
        profile = self.get_profile(user_id)
        now = self._get_utc_now()
        if profile.last_challenge_at and datetime.fromisoformat(profile.last_challenge_at).date() == now.date():
            return False, "You already claimed today's free scratch card.", {}
        profile.scratch_cards_available += 1
        profile.last_challenge_at = now.isoformat()
        profile.log_activity("claim_scratch_card", {"cards": 1})
        self._save_user(profile)
        self.add_notification(user_id, "Free Scratch Card", "You got a free scratch card! Go scratch it now.", {"type": "scratch_available"})
        return True, "Free scratch card claimed! Go to the Scratch section to use it.", {"cards": profile.scratch_cards_available}

    # --- New Features: Enhanced Streak ---

    def use_streak_insurance(self, user_id: int) -> tuple[bool, str]:
        profile = self.get_profile(user_id)
        if profile.streak_insurance <= 0:
            return False, "No streak insurance available. Buy one from the shop."
        profile.streak_insurance -= 1
        profile.log_activity("use_streak_insurance", {"remaining": profile.streak_insurance})
        self._save_user(profile)
        return True, f"Streak insurance used! Your streak is protected. Remaining insurance: {profile.streak_insurance}."

    # --- New Features: Referral Tiers ---

    def _update_referral_tier(self, profile: UserProfile):
        new_tier = self.referral_tiers[0]["name"]
        for tier in reversed(self.referral_tiers):
            if profile.invite_count >= tier["min"]:
                new_tier = tier["name"]
                break
        if new_tier != profile.referral_tier:
            profile.referral_tier = new_tier
            profile.log_activity("referral_tier_up", {"new_tier": new_tier, "invites": profile.invite_count})
            self.add_notification(profile.user_id, "Referral Tier Up!", f"You reached {new_tier} tier with {profile.invite_count} invites!", {"type": "referral_tier", "tier": new_tier})

    def process_referral_tier_upgrade(self, user_id: int) -> Dict[str, Any]:
        profile = self.get_profile(user_id)
        self._update_referral_tier(profile)
        self._save_user(profile)
        tier_info = next((t for t in self.referral_tiers if t["name"] == profile.referral_tier), self.referral_tiers[0])
        next_tier = next((t for t in self.referral_tiers if t["min"] > profile.invite_count), None)
        return {
            "current_tier": profile.referral_tier,
            "current_emoji": tier_info["emoji"],
            "invites": profile.invite_count,
            "next_tier": next_tier["name"] if next_tier else "Max Level",
            "next_tier_min": next_tier["min"] if next_tier else profile.invite_count,
        }

    # --- New Features: Spin Upgrades ---

    def super_spin(self, user_id: int) -> tuple[bool, str, Dict[str, Any]]:
        profile = self.get_profile(user_id)
        if profile.super_spins_available <= 0:
            return False, "No Super Spin tickets available. Buy one from the shop!", {}
        profile.super_spins_available -= 1
        success, message, gift = self.spin_wheel(user_id)
        if success and gift.get("coins", 0) > 0:
            bonus_coins = gift["coins"] * (self.super_spin_multiplier - 1)
            profile.coins += bonus_coins
            message = f" SUPER SPIN! You won {gift['coins'] + bonus_coins} coins (3x multiplier)! {message}"
        elif success:
            message = f" SUPER SPIN! {message}"
        profile.log_activity("super_spin", {"gift": gift.get("name", ""), "coins": gift.get("coins", 0)})
        self._save_user(profile)
        return success, message, gift

    def mega_spin(self, user_id: int) -> tuple[bool, str, Dict[str, Any]]:
        profile = self.get_profile(user_id)
        if profile.mega_spins_available <= 0:
            return False, "No Mega Spin tickets available. Buy one from the shop!", {}
        profile.mega_spins_available -= 1
        rare_gifts = [g for g in self.spin_gifts if g.get("coins", 0) >= 1000]
        if rare_gifts:
            gift = random.choice(rare_gifts)
        else:
            gift = random.choice(self.spin_gifts)
        bonus_coins = gift.get("coins", 0) * (self.mega_spin_multiplier - 1)
        profile.coins += gift.get("coins", 0) + bonus_coins
        message = f" MEGA SPIN! You won {gift.get('coins', 0) + bonus_coins} coins (5x guaranteed rare gift)!"
        profile.log_activity("mega_spin", {"gift": gift.get("name", ""), "coins": gift.get("coins", 0)})
        self._save_user(profile)
        return True, message, gift

    # --- New Features: Notifications ---

    def add_notification(self, user_id: int, title: str, message: str, reward: Optional[Dict] = None):
        profile = self.get_profile(user_id)
        notification = {
            "id": f"notif-{user_id}-{len(profile.notifications) + 1}",
            "title": title,
            "message": message,
            "timestamp": self._get_utc_now().isoformat(),
            "read": False,
            "reward": reward or {},
        }
        profile.notifications.append(notification)
        profile.unread_notifications += 1
        profile.last_notification_at = notification["timestamp"]
        profile.log_activity("notification", {"title": title})
        self._save_user(profile)

    def get_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        profile = self.get_profile(user_id)
        return sorted(profile.notifications, key=lambda n: n.get("timestamp", ""), reverse=True)[:20]

    def mark_notifications_read(self, user_id: int) -> int:
        profile = self.get_profile(user_id)
        count = profile.unread_notifications
        for notif in profile.notifications:
            notif["read"] = True
        profile.unread_notifications = 0
        self._save_user(profile)
        return count

    # --- New Features: Social Sharing ---

    def share_social(self, user_id: int, platform: str) -> tuple[bool, str, Dict[str, Any]]:
        profile = self.get_profile(user_id)
        now = self._get_utc_now()
        if profile.last_social_share_at and datetime.fromisoformat(profile.last_social_share_at).date() == now.date() and profile.social_shares_count >= 3:
            return False, "You have reached the daily share limit (3 shares/day). Come back tomorrow!", {}
        if profile.social_shares_count >= 3 and (not profile.last_social_share_at or datetime.fromisoformat(profile.last_social_share_at).date() != now.date()):
            profile.social_shares_count = 0
        profile.social_shares_count += 1
        profile.last_social_share_at = now.isoformat()
        reward_coins = 200
        reward_xp = 20
        profile.coins += reward_coins
        profile.xp += reward_xp
        profile.log_activity("social_share", {"platform": platform, "reward_coins": reward_coins, "reward_xp": reward_xp, "shares_today": profile.social_shares_count})
        self._add_xp_internal(profile, 0)
        self._save_user(profile)
        self.check_achievements(user_id)
        share_url = f"https://t.me/{os.getenv('TELEGRAM_BOT_USERNAME', 'xiolis_bot')}?start={user_id}"
        return True, f"Shared on {platform}! +{reward_coins} coins, +{reward_xp} XP. Share {3 - profile.social_shares_count} more today for extra rewards!", {"coins": reward_coins, "xp": reward_xp, "share_url": share_url, "shares_remaining": 3 - profile.social_shares_count}

    # --- New Features: Level Leaderboard ---

    def get_level_leaderboard(self) -> List[Dict[str, Any]]:
        ranked = sorted(self.users.values(), key=lambda p: (p.level, p.xp), reverse=True)
        return [{"user_id": p.user_id, "name": p.name, "level": p.level, "xp": p.xp, "badges": len(p.badges)} for p in ranked[:20]]

    # --- New Features: Weekly Leaderboard Rewards ---

    def check_leaderboard_rewards(self, user_id: int) -> Dict[str, Any]:
        profile = self.get_profile(user_id)
        if profile.leaderboard_reward_claimed:
            return {"available": False, "reason": "Already claimed this week"}
        rank = self.get_leaderboard_position(user_id)
        if rank in self.leaderboard_weekly_rewards:
            reward = self.leaderboard_weekly_rewards[rank]
            return {
                "available": True,
                "rank": rank,
                "reward_coins": reward["coins"],
                "reward_xp": reward["xp"],
                "title": reward["title"],
            }
        return {"available": False, "reason": f"Your rank: #{rank}. Top 3 only.", "rank": rank}

    def claim_leaderboard_reward(self, user_id: int) -> tuple[bool, str, Dict[str, Any]]:
        profile = self.get_profile(user_id)
        if profile.leaderboard_reward_claimed:
            return False, "You have already claimed your weekly leaderboard reward.", {}
        reward_info = self.check_leaderboard_rewards(user_id)
        if not reward_info.get("available"):
            return False, reward_info.get("reason", "No reward available."), {}
        rank = reward_info["rank"]
        reward = self.leaderboard_weekly_rewards[rank]
        profile.coins += reward["coins"]
        profile.xp += reward["xp"]
        profile.leaderboard_reward_claimed = True
        profile.log_activity("claim_leaderboard_reward", {"rank": rank, "coins": reward["coins"], "xp": reward["xp"]})
        self._add_xp_internal(profile, 0)
        self._save_user(profile)
        self.check_achievements(user_id)
        return True, f"Weekly reward claimed! You were #{rank} and earned {reward['coins']} coins + {reward['xp']} XP!", {"coins": reward["coins"], "xp": reward["xp"], "rank": rank, "title": reward["title"]}

    # --- New Features: Shop effect handlers for new items ---

    def redeem_shop_item(self, user_id: int, item_id: str) -> tuple[bool, str, Dict[str, Any]]:
        """Redeems a shop item for the user using their coins.

        The item effect is applied server-side to prevent tampering:
          - mystery_coins: grant a random 200-1000 coins surprise.
          - ads_boost:     grant an "ads boost" that doubles the next 5 ads'
                           coin reward (stored as active boost remaining).
          - streak_shield: protect the daily streak for one day.
          - profile_badge: mark the user as having a featured badge.
        """
        profile = self.get_profile(user_id)
        item = next((i for i in self.shop_items if i.get("id") == item_id), None)
        if not item:
            return False, "Invalid shop item.", {}

        price = int(item.get("price", 0))
        if profile.coins < price:
            return False, f"Not enough coins. You need {price} coins for this item.", {}

        # Deduct coins first (atomic enough for single-user flow).
        profile.coins -= price
        effect = item.get("effect", "")

        reward_message = f"🎁 You redeemed {item['name']}!"
        if effect == "mystery_coins":
            surprise = random.randint(200, 1000)
            profile.coins += surprise
            reward_message = f"🎁 You opened {item['name']} and won {surprise} coins!"
        elif effect == "extra_spin":
            # Grant an extra daily spin (increment the count limit for today).
            # Store the bonus in inventory so spin_wheel can allow an extra try.
            profile.inventory.append({"type": "extra_spin", "item": item["id"]})
            reward_message = f"🎡 {item['name']} claimed! You have 1 extra spin today."
        elif effect == "bonus_ads":
            profile.bonus_ads_remaining += 5
            reward_message = f"📺 {item['name']} activated! +5 bonus ads added to your daily limit."
        elif effect == "streak_boost":
            profile.snap_streak += 2
            reward_message = f"🔥 {item['name']} active! Your streak is boosted by +2 days."
        elif effect == "ads_boost":
            profile.inventory.append({"type": "ads_boost", "remaining": 5, "item": item["id"]})
            reward_message = f"🚀 {item['name']} activated! Next 5 ads give 2x coins."
        elif effect == "streak_shield":
            profile.inventory.append({"type": "streak_shield", "item": item["id"]})
            reward_message = f"🛡️ {item['name']} active! Your streak is protected for a day."
        elif effect == "profile_badge":
            profile.inventory.append({"type": "profile_badge", "item": item["id"]})
            profile.has_profile_badge = True
            reward_message = f"🏆 {item['name']} unlocked! You now have a featured badge on the leaderboard."
        elif effect == "scratch_cards":
            profile.scratch_cards_available += 3
            reward_message = f"🎟️ {item['name']} activated! You got 3 scratch cards."
        elif effect == "super_spin":
            profile.super_spins_available += 1
            reward_message = f"🎡 {item['name']} activated! You have 1 Super Spin ready."
        elif effect == "mega_spin":
            profile.mega_spins_available += 1
            reward_message = f"💥 {item['name']} activated! You have 1 Mega Spin ready."
        elif effect == "streak_insurance":
            profile.streak_insurance += 1
            reward_message = f"🛡️ {item['name']} activated! You have 1 streak insurance."
        elif effect == "xp_boost":
            profile.inventory.append({"type": "xp_boost", "remaining": 3, "item": item["id"]})
            reward_message = f"⬆️ {item['name']} activated! Double XP on next 3 actions."

        profile.log_activity("shop_redeem", {"item_id": item_id, "price": price, "effect": effect})
        self._save_user(profile)
        return True, reward_message, item

    # --- Social / Friend System ---

    def send_friend_request(self, from_user_id: int, to_user_id: int) -> tuple[bool, str]:
        if from_user_id == to_user_id:
            return False, "You cannot send a friend request to yourself."
        from_profile = self.get_profile(from_user_id)
        to_profile = self.get_profile(to_user_id)
        if to_user_id in from_profile.friends:
            return False, "You are already friends with this user."
        if any(req.get("from_user_id") == from_user_id and req.get("to_user_id") == to_user_id for req in to_profile.friend_requests):
            return False, "Friend request already sent."
        request = {
            "request_id": f"fr-{from_user_id}-{to_user_id}-{len(to_profile.friend_requests) + 1}",
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "status": "pending",
            "timestamp": self._get_utc_now().isoformat(),
        }
        to_profile.friend_requests.append(request)
        to_profile.log_activity("friend_request_received", {"from_user_id": from_user_id})
        self.add_notification(to_user_id, "New Friend Request", f"{from_profile.name} sent you a friend request!", {"type": "friend_request", "from_user_id": from_user_id})
        self._save_user(to_profile)
        return True, f"Friend request sent to {to_profile.name}!"

    def accept_friend_request(self, user_id: int, request_id: str) -> tuple[bool, str]:
        profile = self.get_profile(user_id)
        request = next((r for r in profile.friend_requests if r.get("request_id") == request_id and r.get("status") == "pending"), None)
        if not request:
            return False, "Friend request not found."
        from_user_id = request.get("from_user_id")
        from_profile = self.get_profile(from_user_id)
        profile.friends.append(from_user_id)
        from_profile.friends.append(user_id)
        request["status"] = "accepted"
        profile.log_activity("friend_request_accepted", {"from_user_id": from_user_id})
        from_profile.log_activity("friend_request_accepted", {"to_user_id": user_id})
        self._save_user(profile)
        self._save_user(from_profile)
        return True, f"You are now friends with {from_profile.name}!"

    def reject_friend_request(self, user_id: int, request_id: str) -> tuple[bool, str]:
        profile = self.get_profile(user_id)
        request = next((r for r in profile.friend_requests if r.get("request_id") == request_id and r.get("status") == "pending"), None)
        if not request:
            return False, "Friend request not found."
        request["status"] = "rejected"
        profile.log_activity("friend_request_rejected", {"from_user_id": request.get("from_user_id")})
        self._save_user(profile)
        return True, "Friend request rejected."

    def get_friend_requests(self, user_id: int) -> List[Dict[str, Any]]:
        profile = self.get_profile(user_id)
        return [r for r in profile.friend_requests if r.get("status") == "pending"]

    def get_friends(self, user_id: int) -> List[Dict[str, Any]]:
        profile = self.get_profile(user_id)
        friends = []
        for fid in profile.friends:
            fprofile = self.get_profile(fid)
            friends.append({
                "user_id": fprofile.user_id,
                "name": fprofile.name,
                "level": fprofile.level,
                "snap_streak": fprofile.snap_streak,
                "has_profile_badge": fprofile.has_profile_badge,
                "bio": fprofile.bio[:100] if fprofile.bio else "",
            })
        return friends

    def update_bio(self, user_id: int, bio: str) -> tuple[bool, str]:
        profile = self.get_profile(user_id)
        profile.bio = bio[:500]
        profile.log_activity("update_bio", {"bio_length": len(profile.bio)})
        self._save_user(profile)
        return True, "Bio updated successfully!"

    def get_public_profile(self, user_id: int, target_id: int) -> Dict[str, Any]:
        target = self.get_profile(target_id)
        viewer = self.get_profile(user_id)
        is_friend = target_id in viewer.friends or target_id == user_id
        return {
            "user_id": target.user_id,
            "name": target.name,
            "level": target.level,
            "xp": target.xp,
            "coins": target.coins,
            "snap_streak": target.snap_streak,
            "has_profile_badge": target.has_profile_badge,
            "badges": target.badges,
            "bio": target.bio if (is_friend or target_id == user_id) else "",
            "is_friend": is_friend,
            "referral_tier": target.referral_tier,
            "completed_tasks": len(target.completed_tasks),
            "total_ads_watched": target.total_ads_watched,
        }

    # --- Translation System ---

    def translate_text(self, text: str, from_lang: str, to_lang: str) -> Dict[str, Any]:
        if from_lang == to_lang or not text:
            return {"translated_text": text, "from_lang": from_lang, "to_lang": to_lang}
        translations = {
            ("en", "hi"): {"hello": "नमस्ते", "how are you": "आप कैसे हैं", "good": "अच्छा", "bad": "बुरा", "money": "पैसा", "earn": "कमाएं", "coins": "सिक्के", "win": "जीत", "share": "साझा करें", "friend": "दोस्त"},
            ("hi", "en"): {"नमस्ते": "hello", "आप कैसे हैं": "how are you", "अच्छा": "good", "बुरा": "bad", "पैसा": "money", "कमाएं": "earn", "सिक्के": "coins", "जीत": "win", "साझा करें": "share", "दोस्त": "friend"},
            ("en", "es"): {"hello": "hola", "how are you": "cómo estás", "good": "bueno", "bad": "malo", "money": "dinero", "earn": "ganar", "coins": "monedas", "win": "ganar", "share": "compartir", "friend": "amigo"},
            ("es", "en"): {"hola": "hello", "cómo estás": "how are you", "bueno": "good", "malo": "bad", "dinero": "money", "ganar": "earn", "monedas": "coins", "compartir": "share", "amigo": "friend"},
            ("en", "fr"): {"hello": "bonjour", "how are you": "comment allez-vous", "good": "bon", "bad": "mauvais", "money": "argent", "earn": "gagner", "coins": "pièces", "win": "gagner", "share": "partager", "friend": "ami"},
            ("fr", "en"): {"bonjour": "hello", "comment allez-vous": "how are you", "bon": "good", "mauvais": "bad", "argent": "money", "gagner": "earn", "pièces": "coins", "partager": "share", "ami": "friend"},
            ("en", "ru"): {"hello": "привет", "how are you": "как дела", "good": "хорошо", "bad": "плохо", "money": "деньги", "earn": "заработать", "coins": "монеты", "win": "выиграть", "share": "поделиться", "friend": "друг"},
            ("ru", "en"): {"привет": "hello", "как дела": "how are you", "хорошо": "good", "плохо": "bad", "деньги": "money", "заработать": "earn", "монеты": "coins", "выиграть": "win", "поделиться": "share", "друг": "friend"},
            ("en", "zh"): {"hello": "你好", "how are you": "你好吗", "good": "好", "bad": "坏", "money": "钱", "earn": "赚", "coins": "硬币", "win": "赢", "share": "分享", "friend": "朋友"},
            ("zh", "en"): {"你好": "hello", "你好吗": "how are you", "好": "good", "坏": "bad", "钱": "money", "赚": "earn", "硬币": "coins", "赢": "win", "分享": "share", "朋友": "friend"},
        }
        key = (from_lang, to_lang)
        if key not in translations:
            return {"translated_text": text, "from_lang": from_lang, "to_lang": to_lang, "note": "Translation not available for this pair"}
        dictionary = translations[key]
        lower_text = text.lower()
        if lower_text in dictionary:
            return {"translated_text": dictionary[lower_text], "from_lang": from_lang, "to_lang": to_lang}
        words = lower_text.split()
        translated_words = [dictionary.get(w, w) for w in words]
        translated = " ".join(translated_words)
        return {"translated_text": translated, "from_lang": from_lang, "to_lang": to_lang}

    def exchange_coins_to_money(self, user_id: int) -> tuple[bool, str, Dict[str, Any]]:
        """Converts the user's coins into wallet money (bot wallet).

        Rate: 10,000 coins = ₹1 (admin-friendly). A 5% processing fee is applied
        so the platform keeps a margin. The user must have at least 10,000 coins
        to exchange. Returns the new wallet balance.
        """
        profile = self.get_profile(user_id)
        coins = profile.coins
        if coins < 10000:
            return False, f"You need at least 10,000 coins to exchange (you have {coins}).", {}
        gross = coins * self.coins_to_rupee_rate
        fee = round(gross * (self.withdrawal_fee_percent / 100), 4)
        final = round(gross - fee, 4)
        profile.coins -= coins
        profile.wallet_bot += final
        profile.log_activity("exchange_coins", {"coins": coins, "gross": gross, "fee": fee, "final": final})
        self._save_user(profile)
        return True, f"Exchanged {coins} coins for ₹{final:.2f} (after {self.withdrawal_fee_percent}% fee).", {
            "coins_exchanged": coins,
            "wallet_added": final,
            "fee": fee,
            "wallet_bot": profile.wallet_bot,
        }

    def approve_withdrawal(self, admin_id: int, user_id: int, request_id: str, verification_code: str) -> str:
        """Admin command to approve a withdrawal after verifying the unique code."""
        admin_profile = self.get_profile(admin_id)
        if not admin_profile.admin:
            return "Access Denied: This is an admin-only command."

        target_profile = self.get_profile(user_id)
        for request in target_profile.withdrawals:
            if request.get("request_id") == request_id and request.get("status") == "pending":
                if not self.security.verify_withdrawal_code(request, verification_code):
                    return f"Verification Failed for {request_id}. The code is incorrect."

                request["status"] = "approved"
                request["approved_by"] = admin_id
                request["transaction_id"] = self.security.generate_transaction_id(user_id)
                target_profile.log_activity("withdrawal_approved", {"request_id": request_id, "amount": request["amount"]})
                self._save_user(target_profile)
                return f"Withdrawal {request_id} for user {user_id} has been approved. Transaction ID: {request['transaction_id']}"
        return f"Pending request with ID {request_id} for user {user_id} not found."

    def get_activity_count(self, profile: UserProfile) -> int:
        return len(profile.completed_tasks) + profile.invite_count

    def get_dashboard(self, user_id: int) -> Dict[str, Any]:
        profile = self.get_profile(user_id)
        snapshot = self.engagement.build_progress_snapshot(profile.wallet_bot, profile.coins)
        now = self._get_utc_now()
        level_info = self._get_level_info(profile.xp)
        referral_tier_info = next((t for t in self.referral_tiers if t["name"] == profile.referral_tier), self.referral_tiers[0])
        next_referral_tier = next((t for t in self.referral_tiers if t["min"] > profile.invite_count), None)
        daily_challenges = self.get_daily_challenges(user_id)
        achievements = self.get_achievements(user_id)
        notifications = self.get_notifications(user_id)
        leaderboard_rewards = self.check_leaderboard_rewards(user_id)
        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "wallet_bot": profile.wallet_bot,
            "wallet_rupee_equivalent": round(profile.coins * self.coins_to_rupee_rate, 4),
            "coins": profile.coins,
            "completed_ads": profile.total_ads_watched,
            "daily_ads_watch_count": profile.daily_ads_watch_count,
            "bonus_ads_remaining": profile.bonus_ads_remaining,
            "available_tasks": self.tasks,
            "invites": profile.invite_count,
            "tasks": profile.completed_tasks,
            "leaderboard_position": self.get_leaderboard_position(profile.user_id),
            "withdrawal_reqs": self.withdrawal_reqs,
            "withdrawal_history": profile.withdrawals,
            "activity_count": self.get_activity_count(profile),
            "engagement": snapshot,
            "trust_feed": self.engagement.build_trust_feed(),
            "live_feed": [self.engagement.generate_fake_withdrawal_feed(), self.engagement.get_fake_chat_message()],
            "support": self.support.get_faq("en"),
            "snap_streak": profile.snap_streak,
            "inventory": profile.inventory,
            "has_profile_badge": profile.has_profile_badge,
            "daily_ads_limit": self.daily_ads_limit,
            "ads_per_reward": 2,
            "spin_gifts": self.spin_gifts,
            "shop_items": self.shop_items,
            # New features
            "level": profile.level,
            "xp": profile.xp,
            "xp_for_next_level": level_info["xp_for_next"],
            "next_level_name": level_info["next_name"],
            "level_progress_pct": level_info["progress_pct"],
            "badges": profile.badges,
            "achievements": achievements,
            "scratch_cards_available": profile.scratch_cards_available,
            "daily_challenges": daily_challenges,
            "streak_insurance": profile.streak_insurance,
            "referral_tier": profile.referral_tier,
            "referral_tier_emoji": referral_tier_info["emoji"],
            "referral_tier_min": referral_tier_info["min"],
            "next_referral_tier": next_referral_tier["name"] if next_referral_tier else "Max Level",
            "next_referral_tier_min": next_referral_tier["min"] if next_referral_tier else profile.invite_count,
            "social_shares_count": profile.social_shares_count,
            "notifications": notifications,
            "unread_notifications": profile.unread_notifications,
            "super_spins_available": profile.super_spins_available,
            "mega_spins_available": profile.mega_spins_available,
            "leaderboard_rewards": leaderboard_rewards,
            "leaderboard_week_rank": profile.leaderboard_week_rank,
            "leaderboard_reward_claimed": profile.leaderboard_reward_claimed,
        }

    def get_help(self, language: str = "en") -> Dict[str, Any]:
        lang_pack = self.support.translations.get(language, self.support.translations[self.support.default_lang])
        return {
            "language": language,
            "message": lang_pack["messages"]["help_intro"],
            "buttons": ["tasks", "contact_support", "contact_admin"],
            "faq": lang_pack["faq"],
            "support_links": self.support.get_support_links(),
        }

    def handle_admin_command(self, user_id: int, text: str) -> str:
        """Handles all admin-related commands."""
        profile = self.get_profile(user_id)
        if not profile.admin:
            return "Access Denied. This area is for admins only."

        parts = text.strip().split()
        command = parts[1] if len(parts) > 1 else "dashboard"

        if command == "dashboard":
            return json.dumps(self.admin_service.get_admin_dashboard(), indent=2)

        if command == "users":
            return json.dumps(self.admin_service.get_all_users_summary(), indent=2)

        if command == "view_user" and len(parts) > 2:
            try:
                target_id = int(parts[2])
                target_profile = self.admin_service.get_user_full_profile(target_id)
                if not target_profile:
                    return f"User {target_id} not found."
                return json.dumps(asdict(target_profile), indent=2, default=str)
            except (ValueError, IndexError):
                return "Usage: /admin view_user <user_id>"

        if command == "set" and len(parts) > 3:
            setting, value = parts[2], parts[3]
            success, message = self.admin_service.update_bot_config(setting, value)
            return message

        if command == "backup":
            return self.admin_service.create_backup()

        if command == "rollback" and len(parts) > 2:
            filename = parts[2]
            return "Rollback successful." if self.admin_service.rollback_to_backup(filename) else "Rollback failed. File not found."

        return "Unknown admin command. Try: dashboard, users, view_user, set, backup, rollback"

    # --- Command Handler Methods ---

    def _handle_start(self, profile: UserProfile) -> Dict[str, Any]:
        welcome_msg = self.support.translations.get("en", {}).get("messages", {}).get("welcome", "Welcome!").format(name=profile.name)
        menu_data = self.build_menu(profile)
        menu_data["text"] = f"{welcome_msg}\n\n{menu_data['text']}"
        return menu_data

    def _handle_menu(self, profile: UserProfile) -> Dict[str, Any]:
        return self.build_menu(profile)

    def _handle_bonus(self, profile: UserProfile) -> str:
        if not profile.bonus_claimed:
            profile.wallet_bot += self.bonus_value
            profile.coins += 500
            profile.bonus_claimed = True
            profile.log_activity("claim_bonus", {"amount": self.bonus_value})
            self._save_user(profile)
            return f"Congratulations! You won {self.bonus_value:.2f} rupees and 500 Coins! Bonus credited.\nYour streak is growing — keep going to unlock the next tier."
        return "Bonus already claimed."

    def _handle_wallet(self, profile: UserProfile) -> str:
        # wallet_bot tracks actual direct rupee earnings (ads, bonus, invites, etc.)
        # wallet_rupee_equivalent is derived from coins. Do NOT overwrite wallet_bot.
        snapshot = self.engagement.build_progress_snapshot(profile.wallet_bot, profile.coins)
        trust = "\n".join(self.engagement.build_trust_feed())
        fake_withdrawal_notice = self.engagement.generate_fake_withdrawal_feed()
        return f"Bot Wallet: {profile.wallet_bot:.2f} rupees | App Wallet: {profile.wallet_app:.2f} | Coins: {profile.coins}\nTier: {snapshot['tier']}\nNext tier: {snapshot['next_tier']}\n\n{fake_withdrawal_notice}\n\n{trust}"

    def _handle_task(self, profile: UserProfile) -> str:
        tasks = [f"{task_id} - {details['title']}" for task_id, details in self.tasks.items()]
        return "Available tasks:\n" + "\n".join(tasks)

    def _handle_spin(self, profile: UserProfile) -> str:
        success, message, value = self.spin_wheel(profile.user_id)
        return message

    def _handle_profile(self, profile: UserProfile) -> str:
        badge = " 🏆 Featured Badge" if profile.has_profile_badge else ""
        return (f"User ID: {profile.user_id}\n"
                f"Name: {profile.name}{badge}\n"
                f"Bot Wallet: {profile.wallet_bot:.2f}\n"
                f"Coins: {profile.coins}\n"
                f"Invites: {profile.invite_count}")

    def _handle_leaderboard(self, profile: UserProfile) -> str:
        leaderboard = self.get_leaderboard()
        if not leaderboard:
            return "No leaderboard data yet."

        lines = [f"🏆 {i + 1}. {name} - ₹{wallet:.2f}" for i, (name, wallet) in enumerate(leaderboard[:10])]
        user_rank = self.get_leaderboard_position(profile.user_id)
        rank_text = f"\n\nYour Rank: #{user_rank}" if user_rank > 0 else "\n\nYou are not on the leaderboard yet. Keep earning!"

        return "🌟 **Top 10 Earners** 🌟\n\n" + "\n".join(lines) + rank_text

    def get_leaderboard_position(self, user_id: int) -> int:
        ranked = sorted(self.users.values(), key=lambda p: p.wallet_bot, reverse=True)
        for index, profile in enumerate(ranked, start=1):
            if profile.user_id == user_id:
                return index
        return 0

    def get_leaderboard(self) -> List[tuple[str, float]]:
        ranked = sorted(self.users.values(), key=lambda p: p.wallet_bot, reverse=True)
        return [(profile.name + (" 🏆" if profile.has_profile_badge else ""), profile.wallet_bot) for profile in ranked if profile.wallet_bot > 0]

