from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.core import BotEngine, UserProfile


class AdminPanelService:
    """
    Manages all administrative tasks, including user management, configuration, and data backups.
    Phase 3: Major upgrade with full admin controls.
    """
    def __init__(self, engine: BotEngine) -> None:
        self.engine = engine
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

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
            
            self.engine.save() # Persist changes if any
            return True, f"Success: '{setting}' updated to '{value}'."
        except (ValueError, TypeError) as e:
            return False, f"Error updating '{setting}': Invalid value type. {e}"

    def create_backup(self) -> str:
        """Creates a timestamped backup of the main data file."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = self.backup_dir / f"bot_data_{timestamp}.db"
        shutil.copy(self.engine.db_path, backup_file)
        return f"Backup created successfully: {backup_file.name}"

    def list_backups(self) -> List[str]:
        """Lists all available backup files."""
        return sorted([f.name for f in self.backup_dir.glob("*.db")], reverse=True)

    def rollback_to_backup(self, filename: str) -> bool:
        """Restores the bot's state from a backup file."""
        backup_file = self.backup_dir / filename
        if not backup_file.exists():
            return False
        shutil.copy(backup_file, self.engine.db_path)
        self.engine.load()  # Reload the engine with the restored data
        return True

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
        self.engine.save()
        return True, f"User {user_id}'s profile updated successfully."

    def get_user_registrations_over_time(self) -> List[Dict[str, Any]]:
        """
        Retrieves the count of new user registrations grouped by date.
        """
        registrations_data = []
        try:
            conn = sqlite3.connect(self.engine.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATE(registered_at) as registration_date, COUNT(user_id) as new_users
                FROM users WHERE registered_at IS NOT NULL
                GROUP BY registration_date ORDER BY registration_date;
            """)
            for row in cursor.fetchall():
                registrations_data.append({"date": row[0], "count": row[1]})
            conn.close()
        except sqlite3.Error as e:
            self.engine.logger.error(f"Error fetching user registrations over time: {e}") # Assuming logger is available
        return registrations_data

    def get_total_coin_balance_over_time(self) -> List[Dict[str, Any]]:
        """
        Calculates the total coin balance of all users over time based on activity logs.
        NOTE: This is computationally intensive. For a large number of users,
        this should be replaced with a separate, pre-calculated statistics table.
        """
        all_events = []
        for user in self.engine.users.values():
            for log in user.activity_log:
                timestamp_str = log.get("timestamp")
                coin_change = 0
                if "reward_coins" in log:
                    coin_change = log["reward_coins"]
                elif log.get("action") == "spin_win" and "coins_won" in log:
                    coin_change = log["coins_won"]
                
                if coin_change > 0 and timestamp_str:
                    all_events.append((datetime.fromisoformat(timestamp_str), coin_change))

        all_events.sort(key=lambda x: x[0])

        balance_over_time = {}
        running_total = 0
        for dt, change in all_events:
            running_total += change
            date_str = dt.strftime('%Y-%m-%d')
            balance_over_time[date_str] = running_total
        
        # Convert to list of dicts for Chart.js
        chart_data = [{"date": date, "total_coins": total} for date, total in balance_over_time.items()]
        return sorted(chart_data, key=lambda x: x['date'])
