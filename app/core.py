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

    def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []

    def replace_one(self, filter_: Dict[Any, Any], doc: Any, upsert: bool = True) -> None:
        key = filter_.get("_id")
        if key is not None:
            self._docs[key] = doc
        elif upsert:
            self._docs[doc.get("_id", self._auto_id)] = doc
            self._auto_id += 1


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

        if profile.daily_ads_watch_count >= self.daily_ads_limit:
            return False, "Daily ads limit reached. Come back after 12 PM or tomorrow."

        reward_coins = random.randint(self.ads_reward_coins_min, self.ads_reward_coins_max)
        reward_money = self.ads_reward_per_ad  # ₹0.002 per completed ad

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

    def spin_wheel(self, user_id: int) -> tuple[bool, str, float]:
        """Handles the logic for the spin wheel, including daily limits."""
        profile = self.get_profile(user_id)
        now = self._get_utc_now()

        last_spin_time = datetime.fromisoformat(profile.last_spin_at) if profile.last_spin_at else None
        if last_spin_time and last_spin_time.date() < now.date():
            profile.daily_spin_count = 0

        if profile.daily_spin_count >= self.daily_spin_limit:
            return False, "You have already used your daily spin. Come back tomorrow!", 0.0

        profile.daily_spin_count += 1
        profile.last_spin_at = now.isoformat()

        value = random.choice(self.spin_values)
        if value == 0.0:
            self._save_user(profile)
            return True, "No luck this time, try again tomorrow.", 0.0

        coins_won = int(value * 10000)
        profile.coins += coins_won
        profile.log_activity("spin_win", {"amount": value, "coins_won": coins_won})
        self._save_user(profile)
        return True, f"Congratulations! You won {coins_won} coins (worth ₹{value:.2f}).", value

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
        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "wallet_bot": profile.wallet_bot,
            "wallet_rupee_equivalent": round(profile.coins * self.coins_to_rupee_rate, 4),
            "coins": profile.coins,
            "completed_ads": profile.total_ads_watched,
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
            "daily_ads_limit": self.daily_ads_limit,
            "ads_per_reward": 2,
            "spin_gifts": self.spin_gifts,
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
        profile.wallet_bot = round((profile.coins * self.coins_to_rupee_rate), 4)
        self._save_user(profile)
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
        return (f"User ID: {profile.user_id}\n"
                f"Name: {profile.name}\n"
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
        return [(profile.name, profile.wallet_bot) for profile in ranked if profile.wallet_bot > 0]

