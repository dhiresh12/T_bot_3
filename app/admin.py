from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pymongo.errors import PyMongoError

if TYPE_CHECKING:
    from app.core import BotEngine, UserProfile


class AdminPanelService:
    """
    Manages all administrative tasks, including user management, configuration, and data backups.
    Phase 3: Major upgrade with full admin controls.
    """
    def __init__(self, engine: BotEngine) -> None:
        self.engine = engine

    def get_admin_dashboard(self) -> Dict[str, object]:
        active_users = len(self.engine.users)
        total_wallet = sum(p.wallet_bot + p.wallet_app for p in self.engine.users.values())
        return {
            "active_users": active_users,
            "total_wallet_balance": round(total_wallet, 2),
            "leaderboard": self.engine.get_leaderboard()[:5],
            "pending_withdrawals": self._pending_withdrawals(),
        }

    def _pending_withdrawals(self) -> List[Dict[str, object]]:
        result = []
        for profile in self.engine.users.values():
            for request in profile.withdrawals:
                if request.get("status") == "pending":
                    result.append(
                        {
                            "user_id": profile.user_id,
                            "request_id": request.get("request_id"),
                            "amount": request.get("amount"),
                        }
                    )
        return result

    def get_all_users_summary(self) -> List[Dict[str, Any]]:
        """Returns a summary list of all users."""
        return [
            {
                "user_id": p.user_id,
                "name": p.name,
                "wallet_bot": round(p.wallet_bot, 4),
                "coins": p.coins,
                "invite_count": p.invite_count,
                "is_admin": p.admin,
            }
            for p in self.engine.users.values()
        ]

    def get_user_full_profile(self, user_id: int) -> Optional[UserProfile]:
        """Returns the complete, unaltered profile of a single user."""
        return self.engine.users.get(user_id)

    def update_bot_config(self, setting: str, value: Any) -> tuple[bool, str]:
        """Updates a configuration attribute in the BotEngine."""
        if not hasattr(self.engine, setting):
            return False, f"Error: Setting '{setting}' does not exist."
        
        try:
            # Get the original type to cast the new value correctly
            original_value = getattr(self.engine, setting)
            value_type = type(original_value)
            
            # Handle special cases like dictionaries
            if isinstance(original_value, dict):
                # For now, we only support replacing the whole dict
                if not isinstance(value, dict):
                    return False, f"Error: Setting '{setting}' must be a valid JSON object."
                setattr(self.engine, setting, value)
            else:
                setattr(self.engine, setting, value_type(value))
            
            # No global save needed for MongoDB, changes are per-user
            return True, f"Success: '{setting}' updated to '{value}'."
        except (ValueError, TypeError) as e:
            return False, f"Error updating '{setting}': Invalid value type. {e}"

    def create_backup(self) -> str:
        """Backup functionality is now handled by the MongoDB provider (e.g., Atlas, Render)."""
        return "Backup functionality is managed by your MongoDB hosting provider (e.g., Atlas snapshots)."

    def list_backups(self) -> List[str]:
        """Backup functionality is now handled by the MongoDB provider."""
        return ["Please check your MongoDB provider for backups."]

    def rollback_to_backup(self, filename: str) -> bool:
        """Rollback functionality is now handled by the MongoDB provider."""
        return False

    def edit_user_profile(self, user_id: int, updates: Dict[str, Any]) -> tuple[bool, str]:
        """Edits a user's profile with the given updates."""
        profile = self.get_user_full_profile(user_id)
        if not profile:
            return False, f"User {user_id} not found."
        for key, value in updates.items():
            if hasattr(profile, key):
                try:
                    # Cast value to the correct type
                    attr_type = type(getattr(profile, key))
                    setattr(profile, key, attr_type(value))
                except (ValueError, TypeError):
                    return False, f"Invalid value type for '{key}'."
            else:
                return False, f"Profile has no attribute '{key}'."
        self.engine._save_user(profile)
        return True, f"User {user_id}'s profile updated successfully."

    def get_user_registrations_over_time(self) -> List[Dict[str, Any]]:
        """
        Retrieves the count of new user registrations grouped by date.
        """
        registrations_data = []
        pipeline = [
            {"$match": {"registered_at": {"$ne": None}}},
            {
                "$project": {
                    "registration_date": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": "$registered_at"}}
                    }
                }
            },
            {"$group": {"_id": "$registration_date", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
            {"$project": {"date": "$_id", "count": "$count", "_id": 0}}
        ]
        try:
            registrations_data = list(self.engine.users_collection.aggregate(pipeline))
        except PyMongoError as e:
            logging.error(f"Error fetching user registrations from MongoDB: {e}")
        return registrations_data

    def get_total_coin_balance_over_time(self) -> List[Dict[str, Any]]:
        """
        Calculates the total coin balance of all users over time based on activity logs.
        NOTE: This is computationally intensive. For a large number of users,
        this should be replaced with a separate, pre-calculated statistics table.
        """
        pipeline = [
            {"$unwind": "$activity_log"},
            {"$match": {"activity_log.action": {"$in": ["complete_task", "watch_ad", "spin_win"]}}},
            {
                "$project": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": "$activity_log.timestamp"}}},
                    "coins_earned": {
                        "$ifNull": [
                            "$activity_log.reward_coins",
                            "$activity_log.coins_won",
                            0
                        ]
                    }
                }
            },
            {"$group": {"_id": "$date", "daily_total": {"$sum": "$coins_earned"}}},
            {"$sort": {"_id": 1}},
            {"$project": {"date": "$_id", "total_coins": "$daily_total", "_id": 0}}
        ]
        try:
            daily_earnings = list(self.engine.users_collection.aggregate(pipeline))
            # Create a cumulative sum
            cumulative_total = 0
            for item in daily_earnings:
                cumulative_total += item["total_coins"]
                item["total_coins"] = cumulative_total
            return daily_earnings
        except PyMongoError as e:
            logging.error(f"Error fetching total balance from MongoDB: {e}")
            return []

    def get_user_tier_distribution(self) -> List[Dict[str, Any]]:
        """
        Calculates the distribution of users across different tiers.
        """
        tier_counts: Dict[str, int] = {}
        for user in self.engine.users.values():
            tier = user.tier if user.tier else "Unknown" # Handle cases where tier might be missing
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Convert to list of dicts for Chart.js
        # Sort by a predefined tier order if available, otherwise alphabetically
        tier_order = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Crown", "Conqueror"]
        sorted_tiers = sorted(tier_counts.items(), key=lambda item: tier_order.index(item[0]) if item[0] in tier_order else len(tier_order))

        chart_data = [{"tier": tier, "count": count} for tier, count in sorted_tiers]
        return chart_data
